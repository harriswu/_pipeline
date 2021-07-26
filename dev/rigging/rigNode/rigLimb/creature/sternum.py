import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.jointUtils as jointUtils

import dev.rigging.rigNode.rigLimb.core.coreLimb as coreLimb


class Sternum(coreLimb.CoreLimb):
    TRANSLATE_MULT_ATTR = 'translateMult'
    ROTATE_MULT_ATTR = 'rotateMult'

    UD_ATTR = 'upDown'

    AUTO_BREATHE_ATTR = 'autoBreath'
    AMPLITUDE_ATTR = 'amplitude'
    FREQUENCY_ATTR = 'frequency'
    OFFSET_ATTR = 'offset'

    PUMP_HANDLE_ATTR = 'pumpHandle'

    def __init__(self, **kwargs):
        super(Sternum, self).__init__(**kwargs)
        self._guide_control = None
        self._translate_multiplier = None
        self._rotate_multiplier = None
        self._auto_breathe = None
        self._amplitude = None
        self._frequency = None

        self._ud_attr = None
        self._translate_mult_attr = None
        self._rotate_mult_attr = None
        self._auto_breathe_attr = None
        self._amplitude_attr = None
        self._frequency_attr = None
        self._offset_attr = None

        self._pump_handle_attr = None

    @property
    def translate_mult_attr(self):
        return self._translate_mult_attr

    @property
    def rotate_mult_attr(self):
        return self._rotate_mult_attr

    @property
    def pump_handle_attr(self):
        return self._pump_handle_attr

    def get_build_kwargs(self, **kwargs):
        super(Sternum, self).get_build_kwargs(**kwargs)
        self._guide_control = kwargs.get('guide_control', None)
        self._translate_multiplier = kwargs.get('translate_multiplier', 0)
        self._rotate_multiplier = kwargs.get('rotate_multiplier', 10)
        self._auto_breathe = kwargs.get('auto_breath', True)
        self._amplitude = kwargs.get('amplitude', 0.5)
        self._frequency = kwargs.get('frequency', 5)

    def flip_build_kwargs(self):
        super(Sternum, self).flip_build_kwargs()
        self._guide_control = namingUtils.flip_names(self._guide_control)

    def get_right_build_setting(self):
        super(Sternum, self).get_right_build_setting()
        self._translate_multiplier *= -1

    def add_input_attributes(self):
        super(Sternum, self).add_input_attributes()

        self._translate_mult_attr, self._rotate_mult_attr = attributeUtils.add(self._input_node,
                                                                               [self.TRANSLATE_MULT_ATTR,
                                                                                self.ROTATE_MULT_ATTR],
                                                                               attribute_type='float',
                                                                               default_value=[
                                                                                   self._translate_multiplier,
                                                                                   self._rotate_multiplier])

        # add up down attr
        self._ud_attr = attributeUtils.add(self._input_node, self.UD_ATTR, attribute_type='float')[0]

    def create_controls(self):
        super(Sternum, self).create_controls()
        name_info = namingUtils.decompose(self._guide_control)
        ctrl = controlUtils.create(name_info['description'], side=name_info['side'], index=name_info['index'],
                                   limb_index=name_info['limb_index'], sub=False, parent=self._controls_group,
                                   position=self._guide_control, rotate_order=0, manip_orient=None,
                                   lock_hide=[attributeUtils.ALL[0]] + attributeUtils.ALL[2:])
        # limit transform
        cmds.transformLimits(ctrl, enableTranslationY=[1, 1], translationY=[-2, 2])

        # create decompose matrix to get value
        decompose = cmds.createNode('decomposeMatrix', name=namingUtils.update(ctrl, type='decomposeMatrix',
                                                                               additional_description='ud'))
        attributeUtils.connect(['{0}.{1}'.format(ctrl, controlUtils.LOCAL_MATRIX_ATTR),
                                decompose + '.outputTranslateY'],
                               [decompose + '.inputMatrix', self._ud_attr])
        if self._auto_breathe:
            # add auto breathe attributes
            attributeUtils.add_divider(ctrl, 'autoBreathe')
            self._auto_breathe_attr = attributeUtils.add(ctrl, self.AUTO_BREATHE_ATTR, attribute_type='float',
                                                         value_range=[0, 1])[0]
            self._amplitude_attr, self._frequency_attr = attributeUtils.add(ctrl,
                                                                            [self.AMPLITUDE_ATTR, self.FREQUENCY_ATTR],
                                                                            attribute_type='float',
                                                                            value_range=[0, None],
                                                                            default_value=[self._amplitude,
                                                                                           self._frequency])
            self._offset_attr = attributeUtils.add(ctrl, self.OFFSET_ATTR, attribute_type='float')[0]

        # add to control list
        self._controls.append(ctrl)

    def create_setup_nodes(self):
        super(Sternum, self).create_setup_nodes()
        self._setup_nodes = namingUtils.update_sequence(self._guide_joints, type='joint',
                                                        additional_description=self._additional_description + ['setup'])
        self._setup_nodes = jointUtils.create_chain(self._guide_joints, self._setup_nodes,
                                                    parent_node=self._setup_group)

    def create_setup(self):
        super(Sternum, self).create_setup()
        # pivot rotate setup
        nodeUtils.arithmetic.equation('{0}*{1}'.format(self._ud_attr, self._rotate_mult_attr),
                                      namingUtils.update(self._controls[0], additional_description='pivotRot'),
                                      connect_attr=self._setup_nodes[0] + '.rotateZ')
        # translation setup
        # get original translation value
        tx = cmds.getAttr(self._setup_nodes[1] + '.translateX')
        nodeUtils.arithmetic.equation('{0} + {1}*{2}'.format(tx, self._ud_attr, self._translate_mult_attr),
                                      namingUtils.update(self._controls[0], additional_description='sternumTranslate'),
                                      connect_attr=self._setup_nodes[1] + '.translateX')

        if self._auto_breathe:
            # auto breathe setup
            self.auto_breathe_setup()

    def auto_breathe_setup(self):
        # auto_breathe_val = autoBreathe * sin(time * frequency + offset) * amplitude
        sine_input_attr = nodeUtils.arithmetic.equation('time1.outTime * {0} + {1}'.format(self._frequency_attr,
                                                                                           self._offset_attr),
                                                        namingUtils.update(self._controls[0],
                                                                           additional_description='autoBreatheSine'))
        sine_output_attr = nodeUtils.triangle.sine(sine_input_attr,
                                                   namingUtils.update(self._controls[0], type='sine',
                                                                      additional_description='autoBreathe'))
        # get connect node
        connect_node = controlUtils.get_hierarchy_node(self._controls[0], 'connect')
        nodeUtils.arithmetic.equation('{0} * {1} * {2}'.format(self._auto_breathe_attr, sine_output_attr,
                                                               self._amplitude_attr),
                                      namingUtils.update(self._controls[0], additional_description='autoBreathe'),
                                      connect_attr=connect_node + '.translateY')

    def connect_to_joints(self):
        super(Sternum, self).connect_to_joints()
        for setup_jnt, jnt in zip(self._setup_nodes, self._joints):
            attributeUtils.connect(attributeUtils.TRANSFORM, attributeUtils.TRANSFORM,
                                   driver=setup_jnt, driven=jnt)

    def add_output_attributes(self):
        super(Sternum, self).add_output_attributes()
        self._pump_handle_attr = attributeUtils.add(self._output_node, self.PUMP_HANDLE_ATTR, attribute_type='float')[0]
        
    def connect_limb_info(self):
        super(Sternum, self).connect_limb_info()
        attributeUtils.connect(self._ud_attr, self._pump_handle_attr)

    def get_input_info(self):
        super(Sternum, self).get_input_info()
        self._translate_mult_attr = '{0}.{1}'.format(self._input_node, self.TRANSLATE_MULT_ATTR)
        self._rotate_mult_attr = '{0}.{1}'.format(self._input_node, self.ROTATE_MULT_ATTR)

    def get_output_info(self):
        super(Sternum, self).get_output_info()
        self._pump_handle_attr = '{0}.{1}'.format(self._output_node, self.PUMP_HANDLE_ATTR)
