# ----------------------------------------------------------------------------
# Copyright (c) 2016-2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from .type import SingleInt, Mapping
from qiime2.sdk.result import ResultCollection
from qiime2.core.testing.util import PipelineError


def parameter_only_pipeline(ctx, int1, int2=2, metadata=None):
    identity_with_optional_metadata = ctx.get_action(
        'dummy_plugin', 'identity_with_optional_metadata')
    concatenate_ints = ctx.get_action('dummy_plugin', 'concatenate_ints')

    ints1 = ctx.make_artifact('IntSequence2', [int1, int2, 3])
    ints2, = identity_with_optional_metadata(ints1, metadata)
    ints3, = identity_with_optional_metadata(ints1, metadata)
    more_ints, = concatenate_ints(ints3, ints2, ints1, int1=int1, int2=int2)

    return ints1, more_ints


def typical_pipeline(ctx, int_sequence, mapping, do_extra_thing, add=1):
    split_ints = ctx.get_action('dummy_plugin', 'split_ints')
    most_common_viz = ctx.get_action('dummy_plugin', 'most_common_viz')

    left, right = split_ints(int_sequence)
    if do_extra_thing:
        left = ctx.make_artifact(
            'IntSequence1', [i + add for i in left.view(list)])

    val, = mapping.view(dict).values()
    # Some kind of runtime failure
    if val != '42':
        raise ValueError("Bad mapping")

    left_viz, = most_common_viz(left)
    right_viz, = most_common_viz(right)

    return mapping, left, right, left_viz, right_viz


def optional_artifact_pipeline(ctx, int_sequence, single_int=None):
    optional_artifact_method = ctx.get_action(
        'dummy_plugin', 'optional_artifacts_method')

    if single_int is None:
        # not a nested pipeline, just sharing the ctx object
        single_int = pointless_pipeline(ctx)

    num1 = single_int.view(int)
    ints, = optional_artifact_method(int_sequence, num1)
    return ints


def visualizer_only_pipeline(ctx, mapping):
    no_input_viz = ctx.get_action('dummy_plugin', 'no_input_viz')
    mapping_viz = ctx.get_action('dummy_plugin', 'mapping_viz')

    viz1, = no_input_viz()
    viz2, = mapping_viz(mapping, mapping, 'foo', 'bar')

    return viz1, viz2


def pipelines_in_pipeline(ctx, int_sequence, mapping):
    pointless_pipeline = ctx.get_action('dummy_plugin', 'pointless_pipeline')
    typical_pipeline = ctx.get_action('dummy_plugin', 'typical_pipeline')
    visualizer_only_pipeline = ctx.get_action(
        'dummy_plugin', 'visualizer_only_pipeline')

    results = []
    results += pointless_pipeline()
    typical_results = typical_pipeline(int_sequence, mapping, True)
    results += typical_results
    results += visualizer_only_pipeline(typical_results[0])

    return tuple(results)


def resumable_pipeline(ctx, int_list, int_dict, fail=False):
    """ This pipeline is designed to be called first with fail=True then a
    second time with fail=False. The second call is meant to reuse cached
    results from the first call
    """
    list_of_ints = ctx.get_action('dummy_plugin', 'list_of_ints')
    dict_of_ints = ctx.get_action('dummy_plugin', 'dict_of_ints')

    list_return, = list_of_ints(int_list)
    dict_return, = dict_of_ints(int_dict)

    if fail:
        list_uuids = [str(result.uuid) for result in list_return.values()]
        dict_uuids = [str(result.uuid) for result in dict_return.values()]

        raise ValueError(f'{list_uuids}_{dict_uuids}')

    return list_return, dict_return


def resumable_varied_pipeline(ctx, ints1, ints2, int1, string, metadata,
                              fail=False):
    varied_method = ctx.get_action('dummy_plugin', 'varied_method')
    list_of_ints = ctx.get_action('dummy_plugin', 'list_of_ints')
    dict_of_ints = ctx.get_action('dummy_plugin', 'dict_of_ints')
    identity_with_metadata = ctx.get_action('dummy_plugin',
                                            'identity_with_metadata')
    most_common_viz = ctx.get_action('dummy_plugin', 'most_common_viz')

    ints1_ret, ints2_ret, int1_ret = varied_method(
        ints1, ints2, int1, string)

    list_ret, = list_of_ints(ints1_ret)
    dict_ret, = dict_of_ints(ints1)

    identity_ret, = identity_with_metadata(ints2[0], metadata)

    viz_ret, = most_common_viz(ints2[1])

    if fail:
        uuids = []

        uuids.append([str(result.uuid) for result in ints1_ret.values()])
        uuids.append([str(result.uuid) for result in ints2_ret.values()])
        uuids.append(str(int1_ret.uuid))

        uuids.append([str(result.uuid) for result in list_ret.values()])
        uuids.append([str(result.uuid) for result in dict_ret.values()])

        uuids.append(str(identity_ret.uuid))

        uuids.append(str(viz_ret.uuid))

        raise PipelineError(uuids)

    return (ints1_ret, ints2_ret, int1_ret, list_ret, dict_ret, identity_ret,
            viz_ret)


def resumable_nested_varied_pipeline(ctx, ints1, ints2, int1, string, metadata,
                                     fail=False):
    internal_pipeline = ctx.get_action('dummy_plugin',
                                       'internal_fail_pipeline')
    list_of_ints = ctx.get_action('dummy_plugin', 'list_of_ints')
    dict_of_ints = ctx.get_action('dummy_plugin', 'dict_of_ints')
    identity_with_metadata = ctx.get_action('dummy_plugin',
                                            'identity_with_metadata')
    most_common_viz = ctx.get_action('dummy_plugin', 'most_common_viz')

    list_ret, = list_of_ints(ints1)
    dict_ret, = dict_of_ints(ints1)

    identity_ret, = identity_with_metadata(ints2[0], metadata)

    viz_ret, = most_common_viz(ints2[1])

    try:
        ints1_ret, ints2_ret, int1_ret = internal_pipeline(
            ints1, ints2, int1, string, fail)._result()
    except PipelineError as e:
        uuids = [uuid for uuid in e.uuids]

        uuids.append([str(result.uuid) for result in list_ret.values()])
        uuids.append([str(result.uuid) for result in dict_ret.values()])

        uuids.append(str(identity_ret.uuid))

        uuids.append(str(viz_ret.uuid))

        raise PipelineError(uuids)

    return (ints1_ret, ints2_ret, int1_ret, list_ret, dict_ret, identity_ret,
            viz_ret)


def internal_fail_pipeline(ctx, ints1, ints2, int1, string, fail=False):
    varied_method = ctx.get_action('dummy_plugin', 'varied_method')

    ints1_ret, ints2_ret, int1_ret = varied_method(
        ints1, ints2, int1, string)

    if fail:
        uuids = []

        uuids.append([str(result.uuid) for result in ints1_ret.values()])
        uuids.append([str(result.uuid) for result in ints2_ret.values()])
        uuids.append(str(int1_ret.uuid))

        raise PipelineError(uuids)

    return ints1_ret, ints2_ret, int1_ret


def de_facto_list_pipeline(ctx, kwarg=False, non_proxies=False):
    returns_int = ctx.get_action('dummy_plugin', 'returns_int')
    list_of_ints = ctx.get_action('dummy_plugin', 'list_of_ints')
    num_ints = 3

    ints = []
    for i in range(num_ints):
        ints_ret, = returns_int(i)
        ints.append(ints_ret)

    if non_proxies:
        ints.append(ctx.make_artifact(SingleInt, num_ints + 1))

    if kwarg:
        ret, = list_of_ints(ints=ints)
    else:
        ret, = list_of_ints(ints)

    return ret


def de_facto_dict_pipeline(ctx, kwarg=False, non_proxies=False):
    returns_int = ctx.get_action('dummy_plugin', 'returns_int')
    dict_of_ints = ctx.get_action('dummy_plugin', 'dict_of_ints')
    num_ints = 3

    ints = {}
    for i in range(num_ints):
        ints_ret, = returns_int(i)
        ints[str(i + 1)] = ints_ret

    if non_proxies:
        ints[str(num_ints + 2)] = ctx.make_artifact(SingleInt, num_ints + 1)

    if kwarg:
        ret, = dict_of_ints(ints=ints)
    else:
        ret, = dict_of_ints(ints)

    return ret


def list_pipeline(ctx, ints):
    assert isinstance(ints, list)
    return ([ctx.make_artifact(SingleInt, 4),
             ctx.make_artifact(SingleInt, 5)])


def collection_pipeline(ctx, ints):
    assert isinstance(ints, ResultCollection)
    return {'key1': ctx.make_artifact(SingleInt, 4),
            'key2': ctx.make_artifact(SingleInt, 5)}


def pointless_pipeline(ctx):
    # Use a real type expression instead of a string.
    return ctx.make_artifact(SingleInt, 4)


def failing_pipeline(ctx, int_sequence, break_from='arity'):
    merge_mappings = ctx.get_action('dummy_plugin', 'merge_mappings')

    list_ = int_sequence.view(list)
    if list_:
        integer = list_[0]
    else:
        integer = 0

    # Made here so that we can make sure it gets cleaned up
    wrong_output = ctx.make_artifact(SingleInt, integer)

    if break_from == 'arity':
        return int_sequence, int_sequence, int_sequence
    elif break_from == 'return-view':
        return None
    elif break_from == 'type':
        return wrong_output
    elif break_from == 'method':
        a = ctx.make_artifact(Mapping, {'foo': 'a'})
        b = ctx.make_artifact(Mapping, {'foo': 'b'})
        # has the same key
        merge_mappings(a, b)
    elif break_from == 'no-plugin':
        ctx.get_action('not%a$plugin', 'foo')
    elif break_from == 'no-action':
        ctx.get_action('dummy_plugin', 'not%a$method')
    else:
        raise ValueError('this never works')
