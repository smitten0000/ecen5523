
# parsetab.py
# This file is automatically generated. Do not edit.
_tabversion = '3.2'

_lr_method = 'LALR'

_lr_signature = '\x8bq\x89\xf6g Bk\x15\xbe\x11]\xf7\xf5\x94\xcd'
    
_lr_action_items = {'CONST':([0,1,2,3,6,10,11,13,16,17,18,21,23,28,],[5,5,-2,-6,-7,5,5,5,5,-8,-3,-4,5,-5,]),'NAME':([0,1,2,3,6,10,11,13,16,17,18,21,23,28,],[4,14,-2,-6,-7,14,4,14,14,-8,-3,-4,14,-5,]),'RPAREN':([5,14,15,19,24,25,27,29,],[-12,-13,25,27,-15,-17,-16,-14,]),'NEWLINE':([0,2,3,4,5,6,8,11,12,14,17,18,20,21,22,24,25,26,27,28,29,],[6,-2,-6,-13,-12,-7,6,6,-11,-13,-8,-3,-9,-4,6,-15,-17,-10,-16,-5,-14,]),'EQUALS':([4,],[16,]),'PLUS':([4,5,12,14,15,20,24,25,26,27,29,],[-13,-12,23,-13,23,23,-15,-17,23,-16,-14,]),'LPAREN':([0,1,2,3,6,9,10,11,13,16,17,18,21,23,28,],[1,1,-2,-6,-7,19,1,1,1,1,-8,-3,-4,1,-5,]),'PRINT':([0,2,3,6,11,17,18,21,28,],[10,-2,-6,-7,10,-8,-3,-4,-5,]),'INPUT':([0,1,2,3,6,10,11,13,16,17,18,21,23,28,],[9,9,-2,-6,-7,9,9,9,9,-8,-3,-4,9,-5,]),'MINUS':([0,1,2,3,6,10,11,13,16,17,18,21,23,28,],[13,13,-2,-6,-7,13,13,13,13,-8,-3,-4,13,-5,]),'ENDMARKER':([0,2,3,4,5,6,8,11,12,14,17,18,20,21,22,24,25,26,27,28,29,],[3,-2,-6,-13,-12,17,3,3,-11,-13,-8,-3,-9,-4,3,-15,-17,-10,-16,-5,-14,]),'$end':([2,3,6,7,11,17,18,21,28,],[-2,-6,-7,0,-1,-8,-3,-4,-5,]),}

_lr_action = { }
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = { }
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'expression':([0,1,10,11,13,16,23,],[12,15,20,12,24,26,29,]),'endofstmt':([0,8,11,22,],[2,18,21,28,]),'statements':([0,],[11,]),'statement':([0,11,],[8,22,]),'module':([0,],[7,]),}

_lr_goto = { }
for _k, _v in _lr_goto_items.items():
   for _x,_y in zip(_v[0],_v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = { }
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> module","S'",1,None,None,None),
  ('module -> statements','module',1,'p_module','/home/relsner/ecen5523/repo/compiler/p0parser.py',21),
  ('statements -> endofstmt','statements',1,'p_statements','/home/relsner/ecen5523/repo/compiler/p0parser.py',25),
  ('statements -> statement endofstmt','statements',2,'p_statements','/home/relsner/ecen5523/repo/compiler/p0parser.py',26),
  ('statements -> statements endofstmt','statements',2,'p_statements','/home/relsner/ecen5523/repo/compiler/p0parser.py',27),
  ('statements -> statements statement endofstmt','statements',3,'p_statements','/home/relsner/ecen5523/repo/compiler/p0parser.py',28),
  ('endofstmt -> ENDMARKER','endofstmt',1,'p_endofstmt','/home/relsner/ecen5523/repo/compiler/p0parser.py',40),
  ('endofstmt -> NEWLINE','endofstmt',1,'p_endofstmt','/home/relsner/ecen5523/repo/compiler/p0parser.py',41),
  ('endofstmt -> NEWLINE ENDMARKER','endofstmt',2,'p_endofstmt','/home/relsner/ecen5523/repo/compiler/p0parser.py',42),
  ('statement -> PRINT expression','statement',2,'p_statement_print','/home/relsner/ecen5523/repo/compiler/p0parser.py',46),
  ('statement -> NAME EQUALS expression','statement',3,'p_statement_assign','/home/relsner/ecen5523/repo/compiler/p0parser.py',50),
  ('statement -> expression','statement',1,'p_statement_expr','/home/relsner/ecen5523/repo/compiler/p0parser.py',54),
  ('expression -> CONST','expression',1,'p_expression_const','/home/relsner/ecen5523/repo/compiler/p0parser.py',58),
  ('expression -> NAME','expression',1,'p_expression_name','/home/relsner/ecen5523/repo/compiler/p0parser.py',62),
  ('expression -> expression PLUS expression','expression',3,'p_expression_add','/home/relsner/ecen5523/repo/compiler/p0parser.py',66),
  ('expression -> MINUS expression','expression',2,'p_expression_unarysub','/home/relsner/ecen5523/repo/compiler/p0parser.py',70),
  ('expression -> INPUT LPAREN RPAREN','expression',3,'p_expression_input','/home/relsner/ecen5523/repo/compiler/p0parser.py',74),
  ('expression -> LPAREN expression RPAREN','expression',3,'p_expression_paren','/home/relsner/ecen5523/repo/compiler/p0parser.py',78),
]