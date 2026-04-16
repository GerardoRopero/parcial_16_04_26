parser grammar NoQLParser;

options { tokenVocab = NoQLLexer; }

// PUNTO DE ENTRADA

program
    : statement+ EOF
    ;

statement
    : insertStmt SEMICOLON?
    | findStmt   SEMICOLON?
    | updateStmt SEMICOLON?
    | deleteStmt SEMICOLON?
    ;


// CREATE — INSERT
//
//  Sintaxis:
//    INSERT INTO <colección> <documento>
//    INSERT INTO <colección> [<doc>, <doc>, ...]    ← inserción múltiple
//
//  Ejemplos:
//    INSERT INTO usuarios { "nombre": "Ana", "edad": 30 }
//    INSERT INTO productos [{ "sku": "A1" }, { "sku": "A2" }]

insertStmt
    : INSERT INTO collection
      ( document                       # insertOne
      | LBRACKET documentList RBRACKET # insertMany
      )
    ;

documentList
    : document (COMMA document)*
    ;

// READ — FIND
// 
//  Sintaxis:
//    FIND [SELECT <campos>] FROM <colección>
//         [WHERE <condición>]
//         [SORT BY <campo> [ASC|DESC] (, <campo> [ASC|DESC])* ]
//         [LIMIT <n>]
//         [SKIP <n>]
//
//  Ejemplos:
//    FIND FROM usuarios WHERE edad > 18
//    FIND SELECT nombre, email FROM usuarios WHERE activo == true LIMIT 10
//    FIND FROM pedidos WHERE total BETWEEN 100 AND 500 SORT BY fecha DESC

findStmt
    : FIND selectClause? FROM collection whereClause? sortClause? limitClause? skipClause?
    ;

selectClause
    : SELECT fieldList
    | SELECT STAR
    ;

fieldList
    : field (COMMA field)*
    ;

field
    : ID
    ;

sortClause
    : SORT BY sortField (COMMA sortField)*
    ;

sortField
    : field (ASC | DESC)?
    ;

limitClause
    : LIMIT NUMBER
    ;

skipClause
    : SKIP_KW NUMBER
    ;


// UPDATE
//
//  Sintaxis:
//    UPDATE <colección> SET <asignaciones> [WHERE <condición>]
//
//  Ejemplos:
//    UPDATE usuarios SET activo = false WHERE edad < 18
//    UPDATE productos SET precio += 10, stock -= 5 WHERE categoria == "electronica"
//    UPDATE pedidos SET { "estado": "enviado", "tracking": "XYZ" } WHERE id == "123"

updateStmt
    : UPDATE collection SET updateBody whereClause?
    ;

updateBody
    : assignmentList          # updateByAssignments
    | document                # updateByDocument
    ;

assignmentList
    : assignment (COMMA assignment)*
    ;

assignment
    : field ASSIGN  value   # setField
    | field INC     value   # incField
    | field DEC     value   # decField
    ;


// DELETE
//  Sintaxis:
//    DELETE FROM <colección> [WHERE <condición>]
//
//  Ejemplos:
//    DELETE FROM usuarios WHERE activo == false
//    DELETE FROM logs                        ← elimina toda la colección

deleteStmt
    : DELETE FROM collection whereClause?
    ;


// CLÁUSULA WHERE

whereClause
    : WHERE condition
    ;

condition
    : condition AND_KW condition           # andCondition
    | condition OR  condition              # orCondition
    | NOT condition                        # notCondition
    | LPAREN condition RPAREN              # parenCondition
    | expression                           # exprCondition
    ;

expression
    : field EQ     value                              # eqExpr
    | field NEQ    value                              # neqExpr
    | field LT     value                              # ltExpr
    | field GT     value                              # gtExpr
    | field LTE    value                              # lteExpr
    | field GTE    value                              # gteExpr
    | field LIKE   STRING                             # likeExpr
    | field IN     LPAREN valueList RPAREN            # inExpr
    | field NOT_IN LPAREN valueList RPAREN            # notInExpr
    | field CONTAINS value                            # containsExpr
    | field EXISTS                                    # existsExpr
    | field BETWEEN value AND_KW value                # betweenExpr
    ;


// TIPOS DE DATOS — DOCUMENTOS Y VALORES

document
    : LBRACE (pair (COMMA pair)*)? RBRACE
    ;

pair
    : (STRING | ID) COLON value
    ;

value
    : STRING                                 # stringVal
    | NUMBER                                 # numberVal
    | TRUE                                   # trueVal
    | FALSE                                  # falseVal
    | NULL_LIT                               # nullVal
    | array                                  # arrayVal
    | document                               # documentVal
    | ID                                     # idRefVal
    ;

array
    : LBRACKET (value (COMMA value)*)? RBRACKET
    ;

valueList
    : value (COMMA value)*
    ;

collection
    : ID
    ;
