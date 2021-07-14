import ast

import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import _creation


def equation(expression, template_name, connect_attr=None, force=True):
    """
    Create node connection network base on the expression, only works for 1D input

    TODO: rewrite using pyparsing

    Symbols:
        +:  add
        -:  sub
        *:  multiply
        /:  divide
       **:  power
        ~:  reverse

    Example:
        equation('(pCube1.tx + pCube2.tx)/2')

    Args:
        expression (str): given equation to make the connection
        template_name (str): use this name as a template, the function will change the name type base on the node it use
        connect_attr(str/list): connect the equation to given attrs
        force(bool): force the connection, default is True

    Return:
        output_attr(str): output attribute from the equation node network
    """
    output_attr = Equation.equation(expression, template_name=template_name)

    # connect attrs
    if connect_attr:
        attributeUtils.connect(output_attr, connect_attr, force=force)

    return output_attr


# operation functions
def add(left, right, template_name):
    """
    connect left and right attr with addDoubleLinear node
    """
    is_str_left = isinstance(left, basestring)
    is_str_right = isinstance(right, basestring)

    if is_str_left or is_str_right:
        add_node = _creation.create('addDoubleLinear', namingUtils.update(template_name, type='addDoubleLinear'),
                                    auto_suffix=True)

        for attr_info in zip([left, right], [is_str_left, is_str_right], ['input1', 'input2']):
            if attr_info[1]:
                cmds.connectAttr(attr_info[0], '{0}.{1}'.format(add_node, attr_info[2]))
            else:
                cmds.setAttr('{0}.{1}'.format(add_node, attr_info[2]), attr_info[0])

        return add_node + '.output'
    else:
        return left+right


def multiply(left, right, template_name):
    """
    connect left and right attr with multDoubleLinear node
    """
    is_str_left = isinstance(left, basestring)
    is_str_right = isinstance(right, basestring)

    if is_str_left or is_str_right:
        mult_node = _creation.create('multDoubleLinear', namingUtils.update(template_name, type='multDoubleLinear'),
                                     auto_suffix=True)

        for attr_info in zip([left, right], [is_str_left, is_str_right], ['input1', 'input2']):
            if attr_info[1]:
                cmds.connectAttr(attr_info[0], '{0}.{1}'.format(mult_node, attr_info[2]))
            else:
                cmds.setAttr('{0}.{1}'.format(mult_node, attr_info[2]), attr_info[0])

        return mult_node + '.output'
    else:
        return left+right


def subtract(left, right, template_name):
    """
    connect left and right attr doing left-right equation node
    """
    is_str_left = isinstance(left, basestring)
    is_str_right = isinstance(right, basestring)

    if is_str_left or is_str_right:
        add_node = _creation.create('addDoubleLinear', namingUtils.update(template_name, type='addDoubleLinear'),
                                    auto_suffix=True)

        if is_str_right:
            mult_node = _creation.create('multDoubleLinear', namingUtils.update(template_name, type='multDoubleLinear'),
                                         auto_suffix=True, input2=-1)
            cmds.connectAttr(right, mult_node + '.input1')
            cmds.connectAttr(mult_node + '.output', add_node + '.input2')
        else:
            cmds.setAttr(add_node + '.input2', right)

        if is_str_left:
            cmds.connectAttr(left, add_node + '.input1')
        else:
            cmds.setAttr(add_node + '.input1', left)

        return add_node + '.output'
    else:
        return left - right


def divide(left, right, template_name):
    """
    connect left and right attr with multiplyDivide node
    set operation to divide
    """
    is_str_left = isinstance(left, basestring)
    is_str_right = isinstance(right, basestring)

    if is_str_left or is_str_right:
        divide_node = _creation.create('multiplyDivide', namingUtils.update(template_name, type='multiplyDivide'),
                                       auto_suffix=True, operation=2)

        for attr_info in zip([left, right], [is_str_left, is_str_right], ['input1X', 'input2X']):
            if attr_info[1]:
                cmds.connectAttr(attr_info[0], '{0}.{1}'.format(divide_node, attr_info[2]))
            else:
                cmds.setAttr('{0}.{1}'.format(divide_node, attr_info[2]), attr_info[0])

        return divide_node + '.outputX'
    else:
        return left / float(right)


def power(left, right, template_name):
    """
    connect left and right attr with multiplyDivide node
    set operation to power
    """
    is_str_left = isinstance(left, basestring)
    is_str_right = isinstance(right, basestring)

    if is_str_left or is_str_right:
        pow_node = _creation.create('multiplyDivide', namingUtils.update(template_name, type='multiplyDivide'),
                                    auto_suffix=True, operation=3)

        for attr_info in zip([left, right], [is_str_left, is_str_right], ['input1X', 'input2X']):
            if attr_info[1]:
                cmds.connectAttr(attr_info[0], '{0}.{1}'.format(pow_node, attr_info[2]))
            else:
                cmds.setAttr('{0}.{1}'.format(pow_node, attr_info[2]), attr_info[0])

        return pow_node + '.outputX'
    else:
        return left ** right


def reverse(operand, template_name):
    """
    connect operand attr with reverse node
    """
    if isinstance(operand, basestring):
        rvs_node = _creation.create('reverse', namingUtils.update(template_name, type='reverse'),
                                    auto_suffix=True)
        cmds.connectAttr(operand, rvs_node + '.inputX')
        return rvs_node + '.outputX'
    else:
        return 1 - operand


def u_sub(operand, template_name):
    """
    connect operand attr with multDoubleLinear node
    set input2 to -1
    """
    is_str = isinstance(operand, basestring)
    if is_str:
        mult_node = _creation.create('multDoubleLinear', namingUtils.update(template_name, type='multDoubleLinear'),
                                     auto_suffix=True, input2=-1)

        cmds.connectAttr(operand, mult_node+'.input1')
        return mult_node + '.output'
    else:
        return -operand


# operation map
_BINOP_MAP = {
                ast.Add: add,
                ast.Sub: subtract,
                ast.Mult: multiply,
                ast.Div: divide,
                ast.Pow: power}

_UNARYOP_MAP = {
                ast.USub: u_sub,
                ast.Invert: reverse}


# equation class
class Equation(ast.NodeVisitor):
    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return _BINOP_MAP[type(node.op)](left, right, self.template_name)

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        return _UNARYOP_MAP[type(node.op)](operand, self.template_name)

    def visit_Num(self, node):
        return node.n

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_Attribute(self, node):
        return '{}.{}'.format(node.value.id, node.attr)

    @classmethod
    def equation(cls, expression, **kwargs):
        cls.template_name = kwargs.get('template_name', '')

        tree = ast.parse(expression)
        calc = cls()
        return calc.visit(tree.body[0])
