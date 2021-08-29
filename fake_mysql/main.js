import net from 'net';
import FMS, {consts} from './src/index.js';
import {
 addQuery,
    askForField,
    notifyType
} from "./query.js";

net.createServer((so) => {
 let server = new FMS({
  socket: so,
  banner: "Fake Mysql/1.0",
  onAuthorize: handleAuthorize,
  onCommand: handleCommand
 });
}).listen(3306);

net.createServer((so) => {
 console.log('client connected');
 so.on('end', () => {
  console.log('client disconnected');
 });
 so.on('data', async function(data) {
  let dataS = data.toString().split("%%");
  let seed = parseInt(dataS[0]);
  // console.log(dataS)
  if (dataS[3] === "0"){
   let seedi = parseInt(dataS[1]);
   console.log(dataS)

   let res = await askForField(seed, seedi, dataS[2]);
   // console.log(res);
   so.write(res);
  } else if (dataS[3] === "1"){
   let fieldAndSeedI = parseInt(dataS[2]);
   notifyType(seed, fieldAndSeedI / 80, dataS[1], fieldAndSeedI % 80)
  }
  // console.log(dataS);
 })
 so.on('error', function(data) {
  // console.log(data);
 })
}).listen('/tmp/rand.sock');

console.log("Started server on port 3306");

function handleAuthorize(param) {
 console.log("Auth Info:");
 console.log(param);
 // Yup you are authorized
 return true;
}

function handleCommand({command, extra}) {
 // command is a numeric ID, extra is a Buffer
 switch (command) {
  case consts.COM_QUERY:
   try{
    handleQuery.call(this, extra.toString());
   } catch (e){
    console.log("parsing err")
   }
   break;
  case consts.COM_PING:
   this.sendOK({message: "OK"});
   break;
  case null:
  case undefined:
  case consts.COM_QUIT:
   console.log("Disconnecting");
   this.end();
   break;
  default:
   console.log("Unknown Command: " + command);
   this.sendOK({message: "OK"});
   break;
 }
}

function handleQuery(query) {
 // Take the query, print it out
 console.log("Got Query: " + query);
 let solvedVarsArr = addQuery(query);
 let seedIndex = solvedVarsArr[0];
 if (seedIndex === "BAD_QUERY"){
  console.log("bad seed");
  this.sendOK({message: "OK", affectedRows: 1})
  return;
 }
 let solvedVars = solvedVarsArr[1];
 let fields = [];
 let result = [];
 for (const solvedVarsKey in solvedVars) {
  let type;
  switch (typeof solvedVars[solvedVarsKey]) {
   case "boolean":
    type = consts.MYSQL_TYPE_VARCHAR;
    break;
   case "string":
    type = consts.MYSQL_TYPE_VAR_STRING;
    break;
   case "number":
    type = consts.MYSQL_TYPE_DOUBLE;
  }
  fields.push(this.newDefinition({ name: solvedVarsKey, columnType: type}));
  result.push(solvedVars[solvedVarsKey])
 }
 // Then send it back to the user in table format
 this.sendDefinitions([
  this.newDefinition({ name: 'CorbFuzz_Magic_Code', columnType: consts.MYSQL_TYPE_LONG }),
  this.newDefinition({ name: "Seed_With_Index", columnType: consts.MYSQL_TYPE_LONG }),
  //  ...fields,
 ]);
 this.sendRows([
  [1333333337, seedIndex, ...result]
 ]);
}

