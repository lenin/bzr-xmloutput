
from bzrlib.xml_serializer import elementtree

ET = elementtree

class _E(object):
    """ This is the E factory, taken from http://effbot.org/zone/element-builder.htm """
    def __call__(self, tag, *children, **attrib):
        elem = ET.Element(tag, attrib)
        for item in children:
            if isinstance(item, dict):
                elem.attrib.update(item)
            elif isinstance(item, basestring):
                if len(elem):
                    elem[-1].tail = (elem[-1].tail or "") + item
                else:
                    elem.text = (elem.text or "") + item
            elif ET.iselement(item):
                elem.append(item)
            else:
                raise TypeError("bad argument: %r" % item)
        return elem

    def __getattr__(self, tag):
        return self(tag)
