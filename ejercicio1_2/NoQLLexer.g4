lexer grammar NoQLLexer;

// Palabras clave CRUD

INSERT      : [Ii][Nn][Ss][Ee][Rr][Tt] ;
INTO        : [Ii][Nn][Tt][Oo] ;
FIND        : [Ff][Ii][Nn][Dd] ;
FROM        : [Ff][Rr][Oo][Mm] ;
UPDATE      : [Uu][Pp][Dd][Aa][Tt][Ee] ;
SET         : [Ss][Ee][Tt] ;
DELETE      : [Dd][Ee][Ll][Ee][Tt][Ee] ;

// Cláusulas

WHERE       : [Ww][Hh][Ee][Rr][Ee] ;
SELECT      : [Ss][Ee][Ll][Ee][Cc][Tt] ;
LIMIT       : [Ll][Ii][Mm][Ii][Tt] ;
SORT        : [Ss][Oo][Rr][Tt] ;
BY          : [Bb][Yy] ;
ORDER       : [Oo][Rr][Dd][Ee][Rr] ;
ASC         : [Aa][Ss][Cc] ;
DESC        : [Dd][Ee][Ss][Cc] ;
SKIP_KW     : [Ss][Kk][Ii][Pp] ;

// Operadores de comparación

EQ          : '==' ;
NEQ         : '!=' ;
LT          : '<' ;
GT          : '>' ;
LTE         : '<=' ;
GTE         : '>=' ;
LIKE        : [Ll][Ii][Kk][Ee] ;
IN          : [Ii][Nn] ;
NOT_IN      : [Nn][Oo][Tt] [ \t]+ [Ii][Nn] ;
CONTAINS    : [Cc][Oo][Nn][Tt][Aa][Ii][Nn][Ss] ;
EXISTS      : [Ee][Xx][Ii][Ss][Tt][Ss] ;
BETWEEN     : [Bb][Ee][Tt][Ww][Ee][Ee][Nn] ;
AND_KW      : [Aa][Nn][Dd] ;

// Operadores lógicos

OR          : [Oo][Rr] ;
NOT         : [Nn][Oo][Tt] ;

// Operadores de asignación 

ASSIGN      : '=' ;
INC         : '+=' ;
DEC         : '-=' ;

// Tipos primitivos

TRUE        : 'true' ;
FALSE       : 'false' ;
NULL_LIT    : 'null' ;

// Literales numéricos

NUMBER      : '-'? [0-9]+ ('.' [0-9]+)? ([eE] [+-]? [0-9]+)? ;

// Literales de cadena

STRING      : '"' ( ~["\\\r\n] | '\\' . )* '"'
            | '\'' ( ~['\\\r\n] | '\\' . )* '\''
            ;

// Identificador

ID          : [a-zA-Z_$] [a-zA-Z_$0-9]* ('.' [a-zA-Z_$] [a-zA-Z_$0-9]*)* ;

// Puntuación

LBRACE      : '{' ;
RBRACE      : '}' ;
LBRACKET    : '[' ;
RBRACKET    : ']' ;
LPAREN      : '(' ;
RPAREN      : ')' ;
COMMA       : ',' ;
COLON       : ':' ;
SEMICOLON   : ';' ;
STAR        : '*' ;

// Ignorados 

WS          : [ \t\r\n]+       -> skip ;
LINE_COMMENT: '//' ~[\r\n]*    -> skip ;
BLOCK_COMMENT: '/*' .*? '*/'   -> skip ;
