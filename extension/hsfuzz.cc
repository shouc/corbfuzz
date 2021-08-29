/*
  +----------------------------------------------------------------------+
  | PHP extension for Coverage Bitmap                                    |
  +----------------------------------------------------------------------+
  | Copyright (c) 2020                                                   |
  +----------------------------------------------------------------------+
  | Permission is hereby granted, free of charge, to any person          |
  | obtaining a copy of this software and associated documentation files |
  | (the "Software"), to deal in the Software without restriction,       |
  | including without limitation the rights to use, copy, modify, merge, |
  | publish, distribute, sublicense, and/or sell copies of the Software, |
  | and to permit persons to whom the Software is furnished to do so,    |
  | subject to the following conditions:                                 |
  |                                                                      |
  | The above copyright notice and this permission notice shall be       |
  | included in all copies or substantial portions of the Software.      |
  |                                                                      |
  | THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,      |
  | EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF   |
  | MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND                |
  | NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS  |
  | BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN   |
  | ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN    |
  | CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE     |
  | SOFTWARE.                                                            |
  +----------------------------------------------------------------------+
  | Author: Chaofan Shou <shou@ucsb.edu>                                 |
  +----------------------------------------------------------------------+

*/

#ifdef HAVE_CONFIG_H
# include "config.h"
#endif

#include "php.h"
#include "php_ini.h"
#include "php_hsfuzz.h"
#include "zend_exceptions.h"
#include "ext/standard/info.h"
#include <map>
#include <sstream>
#include <fstream>
#include <sys/socket.h>
#include <sys/un.h>

#define HAVE_HSFUZZ 1
#if HAVE_HSFUZZ
#include "zend_exceptions.h"

zval *get_zval(zend_execute_data *zdata, int node_type, const znode_op *node)
{
    zend_free_op should_free;
    zval* r = zend_get_zval_ptr(zdata->opline, node_type, node, zdata, &should_free, IS_VAR);
    return r;
}
ZEND_BEGIN_MODULE_GLOBALS(hm)
    std::map<size_t, size_t>   hash_map;
    std::ofstream constraint_fd;
ZEND_END_MODULE_GLOBALS(hm)


#ifdef ZTS
#define HM_G(v) TSRMG(hm_globals_id, zend_hm_globals *, v)
#else
#define HM_G(v) (hm_globals.v)
#endif
ZEND_DECLARE_MODULE_GLOBALS(hm)
ZEND_BEGIN_MODULE_GLOBALS(seed)
    int   seed;
    int   seed_copy;
ZEND_END_MODULE_GLOBALS(seed)


#ifdef ZTS
#define SEED_G(v) TSRMG(seed_globals_id, zend_seed_globals *, v)
#else
#define SEED_G(v) (seed_globals.v)
#endif
ZEND_DECLARE_MODULE_GLOBALS(seed)


#define line_number execute_data->opline->lineno
#define bm_loc HM_G(hash_map)[_hash]
#define b_comp(func) \
    {                \
        	char tmp_filename[1<<12];\
	time_t t = time(NULL);\
	sprintf(tmp_filename, "/tmp/cbc/%ld.txt", t); \
    FILE *f = fopen(tmp_filename, "a");\
	if (f == NULL) {\
		php_printf("Error opening file!\n");\
		exit(1);\
	}\
    fprintf(f, "comp:%c%c\n", '0' + Z_TYPE_P(op1), '0' + Z_TYPE_P(op2));\
    fclose(f);\
        func(result, op1, op2); \
        auto is_equal = Z_TYPE_P(result) == IS_TRUE; \
        _hash = is_equal?_hash:_hash+1;        \
        bm_loc += 1; \
        break;\
    }
#define MAX_DEPTH 10
unsigned int count_slash(char* path){
    unsigned int count = 0;
    char* curr_path(path);
    while (*curr_path != 0){
        if (*curr_path == '/')
            count++;
        curr_path++;
    }
    return count;
}

void to_file_path(char* path){
    char* curr_path(path);
    char* last_slash(path);
    while (*curr_path != 0){
        if (*curr_path == '/')
            last_slash = curr_path;
        curr_path++;
    }
    *last_slash = 0;
}

unsigned int FP_SLASH_COUNT;

bool is_too_deep(char* path){
    return imaxabs(count_slash(path) - FP_SLASH_COUNT) > MAX_DEPTH;
}

size_t hash(const char* p, size_t s) {
    size_t result = 0;
    const size_t prime = 17;
    for (size_t i = 0; i < s; ++i) {
        result = p[i] + (result * prime);
    }
    return result;
}
#define CORBFUZZ_MAGIC_NUM 1333333337
#define corbfuzz_ht arr
#define corbfuzz_hav corbfuzz_ht->arData->val
bool is_corbfuzz_query(zval* x){
    if (x->u1.v.u.extra >= 6000){
        return true;
    }
    if (Z_TYPE_P(x) == IS_ARRAY){
        auto arr = Z_ARR_P(x);
        if (Z_TYPE(corbfuzz_hav) == IS_STRING && strcmp(Z_STRVAL(corbfuzz_hav), "1333333337") == 0){
            return true;
        }
    }
    return false;
}

inline std::string get_query_str(zval* symbolic_var) {
    auto arr = Z_ARR_P(symbolic_var);
#define query_zv arr->arData[1].val
    auto query = Z_STRVAL(query_zv);
    auto query_len = Z_STRLEN(query_zv);
    auto query_str = new char[query_len + 1];
    memcpy(query_str, query, query_len);
    query_str[query_len] = '\0';
    std::string _query_str(query_str);
    delete[] query_str;
    return _query_str;
}



#define decl_handler(t) void t(zval* symbolic_var)
#define decr_ref symbolic_var->value.counted->gc.refcount--;

decl_handler(do_int){

}

decl_handler(do_double){

}

decl_handler(do_null){

}
decl_handler(do_bool){

}
decl_handler(do_string){

}
#include <cstdio>
#include <cstdlib>
void notifyType(const std::string& type, int field_c){
    struct sockaddr_un server_addr;

    // setup socket address structure
    bzero(&server_addr,sizeof(server_addr));
    server_addr.sun_family = AF_UNIX;
    strncpy(server_addr.sun_path, "/tmp/rand.sock",sizeof(server_addr.sun_path) - 1);

    // create socket
    auto server_ = socket(PF_UNIX,SOCK_STREAM,0);
    if (!server_) {
        php_printf("socket err");
        return;
    }

    // connect to server
    if (connect(server_,(const struct sockaddr *)&server_addr,sizeof(server_addr)) < 0) {
        php_printf("connect err");
        exit(-1);
    }
    std::string seed_s = std::to_string(SEED_G(seed));
    seed_s = seed_s + "%%" +  type + "%%" + std::to_string(field_c) + "%%1";

    send(server_, seed_s.c_str(), seed_s.size(),0);
    close(server_);
}

void synthesize(zval* symbolic_var, zval* concrete_val){
//    php_printf("Handling CorbFuzz Synthesis\n");

// get seed
//    zend_string *server_str = zend_string_init("_SERVER", sizeof("_SERVER") - 1, 0);
//    zend_is_auto_global(server_str);
//    zval* carrier = zend_hash_str_find(&EG(symbol_table), ZEND_STRL("_SERVER"));
//    zval* seed = zend_hash_str_find(Z_ARRVAL_P(carrier),
//                                    "HTTP_SEED",
//                                    sizeof("HTTP_SEED") - 1);
//    if (seed == nullptr)
//        return;
//
//    char* seed_s = Z_STRVAL_P(seed);
    auto field_c = symbolic_var->u1.v.u.extra - 6000;

    switch (Z_TYPE_P(concrete_val)) {
        case IS_LONG:
            do_int(symbolic_var);
            return notifyType("1", field_c);
        case IS_DOUBLE:
            do_double(symbolic_var);
            return notifyType("2", field_c);
        case IS_UNDEF:
            return do_null(symbolic_var);
        case IS_FALSE:
        case IS_TRUE:
            do_bool(symbolic_var);
            return notifyType("3", field_c);
        case IS_STRING:
            do_string(symbolic_var);
            return notifyType("4", field_c);
        case IS_REFERENCE:
            return synthesize(symbolic_var, Z_REFVAL_P(concrete_val));
    }
}

//todo: add typing here
int generate(int op, zval* symbolic_var, zval* concrete_val, int dir) {
    // todo: we should use a bitvector here in case of string ops!
    // todo: this should be moved to a different place
//    symbolic_var->u1.v.u.extra = 0;
    auto k = symbolic_var->u1.v.u.extra;
    auto decision = SEED_G(seed_copy) & 1;
    switch (decision) {
        case 0: // eq
            ZVAL_COPY(symbolic_var, concrete_val);
            break;
        case 1: // not eq
            ZVAL_LONG(symbolic_var, SEED_G(seed_copy));
            break;
    }
    int cv_type = Z_TYPE_P(concrete_val);
    HM_G(constraint_fd) << op << ',' << symbolic_var << ',' << decision << ',' << (cv_type == IS_LONG ? std::to_string(Z_LVAL_P(concrete_val)) :
        cv_type == IS_TRUE ? "true": cv_type == IS_FALSE? "false": cv_type == IS_STRING ? Z_STRVAL_P(concrete_val) : "unk"
    ) << ','<< dir << ',' << cv_type << '\n';

    symbolic_var->u1.v.u.extra = k;
    SEED_G(seed_copy) = SEED_G(seed_copy) >> 1;
    return decision;
}

int generate_isset(zval* symbolic_var, int ln) {
    auto decision = SEED_G(seed_copy) & 1;
    auto k = symbolic_var->u1.v.u.extra;
    switch (decision) {
        case 0: // defined
            ZVAL_LONG(symbolic_var, SEED_G(seed_copy));
            break;
        case 1: // undefined
            ZVAL_UNDEF(symbolic_var);
            break;
    }
    HM_G(constraint_fd) << "isset," << symbolic_var << ',' << decision << '\n';
    symbolic_var->u1.v.u.extra = k;
    SEED_G(seed_copy) = SEED_G(seed_copy) >> 1;
    return decision;
}

#define is_session(op) op->u1.v.u.extra >= 8 && op->u1.v.u.extra < 6000
#include "zend_exceptions.h"
#include "zend_interfaces.h"
#include "zend_object_handlers.h"
static int conc_collect(zend_execute_data *execute_data)
{

    // collect coverage
    if (EX(func)->op_array.filename == nullptr ||
        !is_too_deep(ZSTR_VAL(EX(func)->op_array.filename))){
        zval* op1 = get_zval(execute_data, execute_data->opline->op1_type, &execute_data->opline->op1);
        zval* op2 = get_zval(execute_data, execute_data->opline->op2_type, &execute_data->opline->op2);
        zval* result = get_zval(execute_data, execute_data->opline->result_type, &execute_data->opline->result);
        // data synthesis
        auto is_op1_sym = is_corbfuzz_query(op1);
        auto is_op2_sym = is_corbfuzz_query(op2);
        if (is_op1_sym && is_op2_sym){

        } else if (is_op1_sym){
            synthesize(op1, op2);
        } else if (is_op2_sym){
            synthesize(op2, op1);
        }
        int decision;
        if (execute_data->opline->opcode != ZEND_ISSET_ISEMPTY_DIM_OBJ && execute_data->opline->opcode != ZEND_ISSET_ISEMPTY_VAR){
            if (is_session(op1) && is_session(op2)){
                ZVAL_LONG(op2, CORBFUZZ_MAGIC_NUM);
                decision = generate(execute_data->opline->opcode, op1, op2, 0);
            } else if (is_session(op1)){
                decision = generate(execute_data->opline->opcode, op1, op2, 0);
            } else if (is_session(op2)){
                decision = generate(execute_data->opline->opcode, op2, op1, 1);
            }
        } else {
            if (is_session(op1)){
                decision = generate_isset(op1, line_number);
            } else if (is_session(op2)){
                decision = generate_isset(op2, line_number);
            }
        }
        auto file_name = EX(func)->op_array.filename;
        char hash_inp[1 << 12]; int hash_inp_len;
        if (file_name == nullptr){
            hash_inp_len = sprintf(hash_inp, "NF@%d", line_number);
        } else {
            hash_inp_len = sprintf(hash_inp, "%s@%d", ZSTR_VAL(file_name), line_number);
        }
        auto _hash = hash(hash_inp, hash_inp_len);

        switch (execute_data->opline->opcode) {
            case ZEND_IS_EQUAL:
            case ZEND_IS_NOT_EQUAL:
            case ZEND_CASE:
                b_comp(is_equal_function)
            case ZEND_IS_IDENTICAL:
            case ZEND_IS_NOT_IDENTICAL:
                b_comp(is_identical_function)
            case ZEND_IS_SMALLER:
                b_comp(is_smaller_function)
            case ZEND_IS_SMALLER_OR_EQUAL:
                b_comp(is_smaller_or_equal_function)
            case ZEND_SPACESHIP:
                // seems no one is using this esoteric bla....
                break;
            case ZEND_ISSET_ISEMPTY_DIM_OBJ:
                b_comp()
        }
    }
    return ZEND_USER_OPCODE_DISPATCH;
}

//static int setter(zend_execute_data *execute_data) moved to php-src
//{
//    zval* op1 = get_zval(execute_data, execute_data->opline->op1_type, &execute_data->opline->op1);
//    zval* result = get_zval(execute_data, execute_data->opline->result_type, &execute_data->opline->result);
//    if (op1->u1.v.u.extra == 8){
//        if (SEED_G(seed) % line_number % 2 == 0){
//            ZVAL_BOOL(result, false);
//        }
//    }
//    ZVAL_BOOL(result, true);
//    return ZEND_USER_OPCODE_DISPATCH;
//}


PHP_MINIT_FUNCTION(hsfuzz)
{
    return SUCCESS;
}

PHP_MSHUTDOWN_FUNCTION(hsfuzz)
{
    return SUCCESS;
}

char COV_FILE_NAME[1 << 12];
PHP_RINIT_FUNCTION(hsfuzz)
{
    HM_G(hash_map).clear();


    zend_string *server_str = zend_string_init("_SERVER", sizeof("_SERVER") - 1, 0);
    zend_is_auto_global(server_str);
    auto carrier = zend_hash_str_find(&EG(symbol_table), ZEND_STRL("_SERVER"));

    zval* seed = zend_hash_str_find(Z_ARRVAL_P(carrier),
                                    "HTTP_SEED",
                                    sizeof("HTTP_SEED") - 1);

    if (seed != nullptr){
        auto seed_s = Z_STRVAL_P(seed);
        SEED_G(seed) = atoi(seed_s);
        SEED_G(seed_copy) = atoi(seed_s);
    } else {
        SEED_G(seed) = -5;
        SEED_G(seed_copy) = -5;
    }

    if (SEED_G(seed) == -5){
        php_printf("SEED_INCORR");
    }

    auto file_path = zend_hash_str_find(Z_ARRVAL_P(carrier),
                                          "SCRIPT_FILENAME",
                                          sizeof("SCRIPT_FILENAME") - 1);
    char* file_path_s = Z_STRVAL_P(file_path);
    FP_SLASH_COUNT = count_slash(file_path_s);
    auto cov_file_loc = zend_hash_str_find(Z_ARRVAL_P(carrier),
                                        "HTTP_COV_LOC",
                                        sizeof("HTTP_COV_LOC") - 1);

    to_file_path(file_path_s);

    if (cov_file_loc == nullptr){
        time_t t = time(nullptr);
        sprintf(COV_FILE_NAME, "%s/cov/%ld.txt", file_path_s, t);
    } else {
        sprintf(COV_FILE_NAME, "%s/cov/%s.txt", file_path_s, Z_STRVAL_P(cov_file_loc));
    }
    char constraints_fn[4098];
    sprintf(constraints_fn, "%s.cons", COV_FILE_NAME);
    HM_G(constraint_fd).open(constraints_fn);

    zend_string *cookie_str = zend_string_init("_COOKIE", sizeof("_COOKIE") - 1, 0);
    zend_is_auto_global(cookie_str);
    auto cookie = zend_hash_str_find(&EG(symbol_table), ZEND_STRL("_COOKIE"));
    cookie->u1.v.u.extra = 600;
    auto cookie_arr = Z_ARRVAL_P(cookie);
    cookie_arr->gc.refcount = 1;
    if (zend_hash_next_index_insert(cookie_arr, file_path)) {
        Z_ADDREF_P(file_path);
    }
    if (zend_hash_next_index_insert(cookie_arr, file_path)) {
        Z_ADDREF_P(file_path);
    }
    cookie_arr->gc.refcount = 2;

//    zend_string *session_str = zend_string_init("_SESSION", sizeof("_SESSION") - 1, 0);
//    zend_is_auto_global(session_str);
//    auto session = zend_hash_str_find(&EG(symbol_table), ZEND_STRL("_SESSION"));
//    session->u1.v.u.extra = 8;
//    auto session_arr = Z_ARRVAL_P(session);
//    session_arr->gc.refcount = 1;
//    if (zend_hash_next_index_insert(Z_ARRVAL_P(session), file_path)) {
//        Z_ADDREF_P(file_path);
//    }
//    session_arr->gc.refcount = 2;


    zend_set_user_opcode_handler(ZEND_IS_EQUAL, conc_collect);
    zend_set_user_opcode_handler(ZEND_IS_NOT_EQUAL, conc_collect);
    zend_set_user_opcode_handler(ZEND_CASE, conc_collect);
    zend_set_user_opcode_handler(ZEND_IS_IDENTICAL, conc_collect);
    zend_set_user_opcode_handler(ZEND_IS_NOT_IDENTICAL, conc_collect);
    zend_set_user_opcode_handler(ZEND_IS_SMALLER, conc_collect);
    zend_set_user_opcode_handler(ZEND_IS_SMALLER_OR_EQUAL, conc_collect);
    zend_set_user_opcode_handler(ZEND_ISSET_ISEMPTY_DIM_OBJ, conc_collect);
    return SUCCESS;
}

PHP_RSHUTDOWN_FUNCTION(hsfuzz)
{
    std::ofstream cov_file;
    cov_file.open(COV_FILE_NAME);
    cov_file << '{';
    for (auto it : HM_G(hash_map))
        cov_file << it.first << ":" << it.second << ",";
    cov_file << '}';
    cov_file.close();
    HM_G(constraint_fd).close();
    return SUCCESS;
}


zend_module_entry hsfuzz_module_entry = {
    STANDARD_MODULE_HEADER,
    PHP_HSFUZZ_EXTNAME,
    NULL,
    PHP_MINIT(hsfuzz),
    PHP_MSHUTDOWN(hsfuzz),
    PHP_RINIT(hsfuzz),
    PHP_RSHUTDOWN(hsfuzz),
    NULL,
    PHP_HSFUZZ_VERSION,
    STANDARD_MODULE_PROPERTIES
};

#ifdef COMPILE_DL_HSFUZZ
extern "C" {
    ZEND_GET_MODULE(hsfuzz)
}
#endif

#endif
