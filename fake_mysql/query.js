import Parser from "node-sql-parser"
import {exec} from "child_process"
import util from "util";
import fs from "fs";
import md5 from "md5";

const opt = {
    database: 'MariaDB'
}


const parseQuery = (query) => {
    const parser = new Parser.Parser();
    return parser.parse(query, opt);
}

const max = (a,b) => {return a > b ? a : b}
const min = (a,b) => {return a < b ? a : b}

const MAX_ROWS = 100;

const getLenHelper = (ast) => {
    let currentAST = ast
    let limit = 0;
    if (currentAST === undefined){
        return 0;
    }

    if (currentAST.limit){
        let val =  currentAST.limit.value;
        limit = val[val.length - 1].value
    } else {
        limit = MAX_ROWS;
    }

    if (currentAST["union"] === 'union'){
        limit += getLenHelper(currentAST["_next"]);
    }


    for (const key in currentAST["from"]) {
        let currentEl;
        if (currentAST["from"].hasOwnProperty(key)){
            currentEl = currentAST["from"][key];
        } else continue;
        if (currentEl.hasOwnProperty("expr") && currentEl.hasOwnProperty("join")){
            switch (currentEl["join"]) {
                case "RIGHT JOIN":
                    limit = getLenHelper(currentEl["expr"].ast);
                    break;
                case "JOIN":
                case "INNER JOIN":
                    limit = min(getLenHelper(currentEl["expr"].ast), limit);
                    break;
            }
        }
    }
    if (currentAST["_limit"]) {
        let val =  currentAST["_limit"].value;
        limit = min(limit, val[val.length - 1].value);
    }
    return limit;
}

const getLen = ast => getLenHelper(ast.ast)

const toColumnStr = (expr, tables) => {
    if (expr.type === 'column_ref'){
        if (expr.table)
            return [expr.table + '.' + expr.column];
        let result = []
        for (let i = 0; i < tables.length; i++) {
            result.push(tables[i] + '.' + expr.column);
        }
        if (tables.length === 1){
            result.push(expr.column);
        }
        return result
    }
    return [expr];
}

const getFieldMapHelper = (field, ast) => {
    let column = ast.columns;
    let from = ast.from;
    let tables = [];
    if (!from){
        return;
    }
    for (let i = 0; i < from.length; i++) {
        let currentEl = from[i];
        // console.log(currentEl)
        tables = currentEl.as != null ? tables.concat([currentEl.table, currentEl.as]) : tables.concat([currentEl.table]);
    }
    if (column === "*"){
        return;
    }
    for (let i = 0; i < column.length; i++) {
        let currentEl = column[i];
        // console.log(currentEl.expr)
        let res = {
            fields: toColumnStr(currentEl.expr, tables),
            name: currentEl.expr.column,
            location: i,
            type: [1,1,1,1],
            symbolic_var: `cf${field.length}`,
        }
        if (currentEl.as){
            res["fields"] = res["fields"].concat( toColumnStr(currentEl.as, tables) )
        }
        field.push(res)
    }
}

const getFieldMap = (ast) => {
    let field = [];
    getFieldMapHelper(field, ast.ast)
    return field;
}

const getCol = (ast) => {
    return ast.columnList.map(v => {
        return v.split("::").splice(1);
    });
}

const assignWhenMorePrior = (priority, type, loc) => {
    if (loc.type[type - 1] > priority){
        return;
    }
    loc.type[type - 1] += priority;
}

const updateTyping = (fields, a, b) => {
    if ((a[0] === -1 && b[0] === -1) || (a[0] !== -1 && b[0] !== -1)){
        return
    }
    if (b[0] === -1) {
        updateTyping(fields, b, a);
    }
    // a is column
    for (let i = 0; i < fields.length; i++) {
        // if (fields[i].name === a[1]){
        //     fields[i].type = b[0];
        //     fields[i].type_priority += 1;
        // }
        if (fields[i].symbolic_var === a[1]){
            assignWhenMorePrior(10, b[0], fields[i])
        }
    }
}

const getConstraint = (ast) => {
    let fields = getFieldMap(ast);
    let where = getConstraintHelper(ast.ast.where, fields);
    let on = [];
    if (!ast.ast.from) return;
    ast.ast.from.forEach((v,k)=> {
        on.push(getConstraintHelper(v.on, fields));
    })
    return [fields, where]
}

const handleCons = (cons) => {
    switch (typeof cons) {
        case "string":
            return '"'+ cons.replace(/(^|[^\\])"/g,'$1\\"')+'"'
        case 'boolean':
            return cons ? 'true' : 'false'
        default:
            return cons
    }
}

const handleConsConstraint = (cons) => {
    switch (cons.type) {
        case 'string':
            return [1, '"'+ cons.value.replace(/(^|[^\\])"/g,'$1\\"')+'"'];
        case 'number':
            return [Number.isInteger(cons.value) ? 2 : 3, cons.value];
        case 'bool':
            return [4, cons.value ? 'true' : 'false'];
    }
}

const findField = (fields, match) => {
    for (let i = 0; i < fields.length; i++) {
        for (let j = 0; j < fields[i].fields.length; j++) {
            if (fields[i].fields[j] === match){
                return true;
            }
        }
    }
    return false;
}

const notifyColumn = (column, fields) => {
    if (column[0] !== -1)
        return;
    for (let i = 0; i < fields.length; i++) {
        for (let j = 0; j < fields[i].fields.length; j++) {
            if (fields[i].fields[j] === column[1]){
                return fields[i].symbolic_var;
            }
        }
    }
    fields.push({
        fields: [column[1]],
        name: column[1],
        location: -1,
        type: [1,1,1,1],
        symbolic_var: `unk${fields.length}`,
    })
    return `unk${fields.length - 1}`
}

const getConstraintHelper = (currentEl, fields) => {
    let constraints = "";
    if (currentEl){
        if (currentEl.type === "binary_expr"){
            switch (currentEl.operator){
                case "&&":
                case "AND":
                case "OR":
                case "||":
                    let leftConstraint = "true"
                    if (currentEl.left.type === 'binary_expr'){
                        leftConstraint = getConstraintHelper(currentEl.left, fields)
                    }
                    let rightConstraint = "true"
                    if (currentEl.right.type === 'binary_expr'){
                        rightConstraint = getConstraintHelper(currentEl.right, fields)
                    }
                    constraints += `(${
                        currentEl.operator === 'OR' || currentEl.operator === '||' ?
                            'or' : 'and'
                    } ${leftConstraint} ${rightConstraint})`
                    break;
                // case "*":
                // case "+":
                // case "-":
                // case "/":
                case "!=":
                case "<":
                case "<=":
                case "<>":
                case ">":
                case ">=":
                case "=":
                    let eqLeft = [-1, '']
                    switch (currentEl.left.type){
                        case 'column_ref':
                            eqLeft[1] = currentEl.left.column;
                            if (currentEl.left.table)
                                eqLeft[1] = `${currentEl.left.table}.${eqLeft[1]}`
                            eqLeft[1] = notifyColumn(eqLeft, fields);
                            break;
                        default:
                            eqLeft = handleConsConstraint(currentEl.left);
                    }

                    let eqRight = [-1, '']
                    switch (currentEl.right.type){
                        case 'column_ref':
                            eqRight[1] = currentEl.right.column;
                            if (currentEl.right.table)
                                eqRight[1] = `${currentEl.right.table}.${eqRight[1]}`
                            eqRight[1] = notifyColumn(eqRight, fields);
                            break;
                        default:
                            eqRight = handleConsConstraint(currentEl.right);
                    }
                    updateTyping(fields, eqLeft, eqRight);

                    return `(${currentEl.operator} ${eqLeft[1]} ${eqRight[1]})`

                // case "?":
                // case "?&":
                // case "?|":
                // case "@>":
                // case "BETWEEN":
                // case "EXISTS":
                // case "IN":
                // case "IS":
                // case "IS NOT":
                // case "LIKE":
                // case "NOT BETWEEN":
                // case "NOT EXISTS":
                // case "NOT IN":
                // case "NULL":

            }
        }
    }
    return constraints;
}

export const getQueryInfo = (query) => {
    let ast;
    try{
        ast = parseQuery(query);
    } catch (e){
        console.log("err");
        return;
    }
    if (ast.ast.type !== "select" || !ast.ast.from){
        return;
    }

    let constraints = getConstraint(ast);
    let row_limit = getLen(ast);
    return {
        constraint: constraints[1],
        fields: constraints[0],
        limit: row_limit,
        extra_constraint: {}
    }
}

const addAnd = (constraint, newCondition) => {
    return `(and ${constraint} ${newCondition})`;
}

const addOr = (constraint, newCondition) => {
    return `(or ${constraint} ${newCondition})`;
}

const getExtraConstraintKey = (types) => {
    return types.join(",")
}

const getExtraConstraint = (queryInfo, types) => {
    // console.log(queryInfo)
    return queryInfo.extra_constraint[getExtraConstraintKey(types)];
}

const sample = (array) => {
    const totalPriority = array.reduce((a,b) => a+b);
    const threshold = Math.random() * totalPriority;
    let k = 0;
    for (let i = 0; i < array.length; i++) {
        k += array[i];
        if (k >= threshold)
            return i;
    }
    return array.length - 1
}

const emitSMT = (queryInfo, types) => {
    let smt = '';
    queryInfo.fields.map((v,k)=> {
        types[k] = (!!types && !!types[k]) ? types[k] : sample(v.type);
        switch (types[k]){
            case 0:
                // string
                smt += `(declare-fun ${v.symbolic_var} () String)`;
                break
            case 1:
                // int
                smt += `(declare-const ${v.symbolic_var} Int)`;
                break
            case 2:
                // real
                smt += `(declare-const ${v.symbolic_var} Real)`;
                break
            case 3:
                smt += `(declare-const ${v.symbolic_var} Bool)`;
                // bool
                break
            default:
                console.log("unknown")
        }
        smt += '\n'
    });
    let extraConstraint = getExtraConstraint(queryInfo, types);
    let constraint = queryInfo.constraint;
    if (extraConstraint){
        for (let i = 0; i < extraConstraint.length; i++) {
            constraint = addAnd(constraint, extraConstraint[i]);
        }
    }
    if (constraint !== " " && constraint !== "")
       smt += `(assert ${constraint})`;
    smt += `\n(set-option :model.completion true)\n(check-sat)\n(get-model)`;
    return smt;
}

const removeLeadingEmpty = (content) => {
    let counter = 0;
    for (let i = 0; i < content.length; i++) {
        if (content[i] !== " "){
            break;
        }
        counter++;
    }
    return content.slice(counter)
}

const parseZ3Result = async (result) => {
    result = result.split("\n");
    if (result.length === 0 || result[0] !== 'sat') return -1;
    let dict = {}
    for (let i = 2; i < result.length - 2; i+=2) {
        let field_raw = removeLeadingEmpty(result[i]).split(' ');
        let result_raw = removeLeadingEmpty(result[i + 1]);
        let symbolic_var = field_raw[1];
        let syn_result = result_raw.slice(0, result_raw.length - 1);
        switch (field_raw[3]){
            case 'Bool':
                syn_result = syn_result === 'true';
                break;
            case 'Real':
                syn_result = parseFloat(syn_result);
                if (isNaN(syn_result)) syn_result = 0.0;
                break;
            case 'Integer':
            case 'Int':
                syn_result = parseInt(syn_result);
                if (isNaN(syn_result)) syn_result = 0;
                break;
            case 'String':
                syn_result = syn_result.slice(1, syn_result.length - 1);
                break
        }
        dict[symbolic_var] = syn_result;
    }
    return dict
}

const executeZ3 = async (code) => {
    let fn = md5(code);
    let filename = `smt/${fn}.smt`
    let wf = util.promisify(fs.writeFile);
    let pe = util.promisify(exec);
    await wf(filename, code);
    let out;
    out = await pe(`z3 ${filename}`)
    // console.log(out)
    return parseZ3Result(out.stdout);
}

const addSynthesizedToConstraint = (queryInfo, dict, types) => {
    let constraints = null;
    for (const k in dict) {
        let currentDict = dict[k]
        if (!constraints){
            constraints = `(not (= ${k} ${handleCons(currentDict)}))`;
            continue
        }
        constraints = addOr(constraints, `(not (= ${k} ${handleCons(currentDict)}))`);
    }
    let constraint_key = getExtraConstraintKey(types);
    if (!queryInfo.extra_constraint[constraint_key]) queryInfo.extra_constraint[constraint_key] = [];
    queryInfo.extra_constraint[constraint_key].push(constraints);
}


// let queryInfo = getQueryInfo('SELECT * from a WHERE Age>32')
//
// addSynthesizedToConstraint(queryInfo, {unk0: 33});
// addSynthesizedToConstraint(queryInfo, {unk0: 34});
// addSynthesizedToConstraint(queryInfo, {unk0: 35});
// addSynthesizedToConstraint(queryInfo, {unk0: 36});
// addSynthesizedToConstraint(queryInfo, {unk0: 37});
// addSynthesizedToConstraint(queryInfo, {unk0: 38});
// console.log(queryInfo)
// // console.log(queryInfo)
// // console.log(emitSMT(queryInfo))
// executeZ3(emitSMT(queryInfo)).then(console.log).catch(console.log)


// CURD

let queries = {};
let cache = {};
let field_cache = {};

const parseSeededQuery = (query) => {
    let seed = "";
    let doneSeed = false;
    let sliceEnd = 0;
    for (let i = query.length - 1; i >= 0; i--) {
        if (query[i] === ';') doneSeed = true;
        if (!doneSeed) seed = query[i] + seed;
        if (doneSeed && query[i] !== ';') {
            sliceEnd = i + 1;
            break;
        }
    }
    return [query.slice(0, sliceEnd), parseInt(seed)]
}

const checkCache = (seed, seedIndex) => {
    return cache[seed] ? cache[seed][seedIndex] ? cache[seed][seedIndex] : {} : {};
}

const isQueryInCache = (seed, queryHash) => {
    let currentCaches = cache[seed];
    for (let i = 0; i < currentCaches.length; i++) {
        if (currentCaches[i].hash === queryHash){
            return i;
        }
    }
    return -1;
}

export const addQuery = (query) => {
    let parsedQ = parseSeededQuery(query);
    let _query = parsedQ[0];
    let seed = parsedQ[1];
    if (isNaN(seed)){
        return ['BAD_QUERY', {}];
    }
    let query_hash = md5(_query);
    if (!queries[query_hash])
        queries[query_hash] = getQueryInfo(_query);
    if (!queries[query_hash]){
        return ['BAD_QUERY', {}];
    }
    let queryInfo = queries[query_hash]
    if (!cache[seed]){
        cache[seed] = [];
    }
    let currentCaches = cache[seed];
    let seedIndex = isQueryInCache(seed, query_hash);
    if (seedIndex === -1) {
        seedIndex = currentCaches.length;
        currentCaches.push({
            qi: JSON.parse(JSON.stringify(queryInfo)),
            vars: {},
            types: [],
            hash: query_hash
        })
    }
    console.log(currentCaches[seedIndex].vars)
    return [seedIndex, currentCaches[seedIndex].vars];
}

const addField = (queryInfo, fieldName) => {
    queryInfo.fields.push({
        fields: [fieldName],
        name: fieldName,
        location: -1,
        type: [1,1,1,1],
        symbolic_var: `new${queryInfo.fields.length}`,
    })
}

const convertField = (queryInfo, types, vars, seed) => {
    let newVars = {};
    for (const varsKey in vars) {
        for (let i = 0; i < queryInfo.fields.length; i++) {
            if (varsKey !== queryInfo.fields[i].symbolic_var){
                continue
            }
            for (let j = 0; j < queryInfo.fields[i].fields.length; j++) {
                if (!field_cache[seed]) field_cache[seed] = [];
                field_cache[seed].push(i)
                newVars[queryInfo.fields[i].fields[j]] = vars[varsKey] + ";"+
                    types[i] + ";" + (field_cache[seed].length - 1)
            }
        }
    }

    return newVars;
}

const RETRY = 10;
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
export const askForField = async (seed, seedIndex, field) => {
    console.log(seed, seedIndex, field)
    console.log(cache);
    let currentCache = cache[seed][seedIndex];
    while (!currentCache){
        await sleep(100);
        currentCache = cache[seed][seedIndex];
    }
    let queryInfo = queries[currentCache.hash]

    if (currentCache.vars[field]){
        return currentCache.vars[field];
    }
    // not a known field
    if (!findField(currentCache.qi.fields, field)){
        addField(currentCache.qi, field);
        addField(queryInfo, field);
    }
    let cter = 0;
    while (cter++ < RETRY){
        try {
            currentCache.vars = await executeZ3(emitSMT(currentCache.qi, currentCache.types));
            if (currentCache.vars === -1) {
                currentCache.vars = {};
                return "UNSAT";
            }
            break;
        } catch (e) {
            currentCache.types = [];
            console.log("retrying")
        }
    }
    console.log(currentCache.vars)
    addSynthesizedToConstraint(queryInfo, currentCache.vars, currentCache.types);
    currentCache.vars = convertField(currentCache.qi, currentCache.types, currentCache.vars, seed);
    if (currentCache.vars[field] === undefined)
        return "123;1;0"
    return currentCache.vars[field];
}

export const notifyType = (seed, seedIndex, typeS, field_c) => {
    let currentCache = cache[seed][seedIndex];
    let queryInfo = queries[currentCache.hash];
    let type = parseInt(typeS);
    // console.log(queryInfo);
    queryInfo.fields[field_cache[seed][parseInt(field_c)]].type[type] += 10;

    
}

// console.log(addQuery("SELECT * FROM `houses` WHERE Area <= 75;1"));
// askForField(1, 0, "a").then(v => console.log(1, v))
// setTimeout(()=>{
//     console.log(addQuery("SELECT * FROM a where c = 1;2"));
//     askForField(2, 0,"a").then(v => console.log(2, v))
// }, 50)
//
// setTimeout(()=>{
//     console.log(addQuery("SELECT * FROM a where c = 1;3"));
//     askForField(3, 0,"a").then(v => console.log(3, v))
// }, 100)
//
