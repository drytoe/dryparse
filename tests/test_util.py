import copy

from dryparse.util import reassignable_property


def create_class_with_reassignable_properties():
    class C:
        @reassignable_property
        def prop1(self) -> str:
            return "prop1_value"

        @reassignable_property
        def prop2(self) -> int:
            return 2

    return C


class TestReassignableProperty:
    def test_essentials(self):
        C = create_class_with_reassignable_properties()
        c = C()
        assert c.prop1 == "prop1_value"
        assert c.prop2 == 2

        c.prop1 = "new"
        assert c.prop1 == "new"

        c.prop2 = lambda instance: instance.prop1
        assert c.prop2 == c.prop1

        c.prop1 = "prop1_new"
        assert c.prop2 == "prop1_new"

    def test_delete(self):
        C = create_class_with_reassignable_properties()
        c = C()
        c.prop1 = "prop1_new"
        assert c.prop1 == "prop1_new"
        del c.prop1
        assert c.prop1 == "prop1_value"

    def test_deepcopy(self):
        C = create_class_with_reassignable_properties()
        c = C()
        d = copy.deepcopy(c)
        assert d.prop1 == "prop1_value"

        c.prop1 = "c_prop1"
        assert d.prop1 == "prop1_value"

        d.prop1 = "d_prop1"
        assert d.prop1 == "d_prop1"
        assert c.prop1 == "c_prop1"

        del d.prop1
        assert d.prop1 == "prop1_value"
        assert c.prop1 == "c_prop1"
