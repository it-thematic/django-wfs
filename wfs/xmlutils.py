'''

  xml utilities base on the lxml library.

'''

from lxml import etree


def parse_xml_base(request):
    params = {}
    xml_str = request.body.decode(request.encoding)
    root = etree.fromstring(xml_str)

    for key, value in root.attrib.items():
        params[key] = value

    request_type = etree.QName(root).localname
    if request_type:
        params['request'] = request_type

    for sub in root:
        name = etree.QName(sub).localname.lower()
        if name == 'typename':
            value = etree.QName(sub.text)
            typename = value.localname
            params['typename'] = typename
    return params


def parse_xml_feature(request):
    params = {}
    xml_str = request.body.decode(request.encoding)
    root = etree.fromstring(xml_str)

    for key, value in root.attrib.items():
        params[key] = value
    request_type = etree.QName(root).localname
    if request_type:
        params['request'] = request_type

    for query in root:
        for key, value in query.attrib.items():
            params[key] = value

        for filter_query in query:
            name = etree.QName(filter_query).localname.lower()
            if name == 'propertyname':
                value = filter_query.text
                params['propertyname'] = value
            elif name == 'filter':
                for filter_type in filter_query:
                    name = etree.QName(filter_type).localname.lower()
                    if name in ['gmlobjectid', 'featureid']:
                        for feature, id in filter_type.attrib.items():
                            params['featureid'] = ','.join([params.get('featureid', ''), '.'.join([params.get('typeName', ''), id])])
                if params.get('featureid'):
                    params['featureid'] = params.get('featureid')[1:]
    return params


def parse_xml_transaction(request):
    params = {}
    xml_str = request.body.decode(request.encoding)
    root = etree.fromstring(xml_str)

    for key, value in root.attrib.items():
        params[key] = value
    request_type = etree.QName(root).localname
    if request_type:
        params['request'] = request_type

    params['transaction_type'] = []
    for transaction_type in root:
        transaction = {}
        name = etree.QName(transaction_type).localname.lower()
        transaction['type'] = name

        if name in ('update', 'delete'):
            for key, value in transaction_type.attrib.items():
                transaction[key] = value

            transaction_property = {}
            transaction['property'] = transaction_property
            property_list = [xml_property for xml_property in transaction_type if etree.QName(xml_property).localname.lower() == 'property']
            for xml_property in property_list:
                prop_name, prop_value = xml_property[0:2]
                if prop_name.text.lower() == 'geometry':
                    transaction_property[prop_name.text] = parse_xml_geometry(prop_value)
                else:
                    transaction_property[prop_name.text] = prop_value.text

            transaction_filter = {}
            transaction['filter'] = transaction_filter
            filter_lists = [xml_filter for xml_filter in transaction_type if etree.QName(xml_filter).localname.lower() == 'filter']
            for filter_list in filter_lists:
                for filter_type in filter_list:
                    name = etree.QName(filter_type).localname.lower()
                    if name in ['gmlobjectid', 'featureid']:
                        for feature, id in filter_type.attrib.items():
                            transaction_filter['featureid'] = ','.join([transaction_filter.get('featureid', ''), id])
                        transaction_filter['featureid'] = transaction_filter['featureid'][1:]
            params['transaction_type'].append(transaction)
        elif name == 'insert':
            for transaction_insert in transaction_type:
                transaction['typeName'] = etree.QName(transaction_insert).localname
                transaction_property = {}
                transaction['property'] = transaction_property
                for xml_property in transaction_insert:
                    prop_name = etree.QName(xml_property).localname.lower()
                    if prop_name == 'geometry':
                        transaction_property[prop_name] = parse_xml_geometry(xml_property)
                    else:
                        transaction_property[prop_name] = xml_property.text
            params['transaction_type'].append(transaction)
    return params


def parse_xml_geometry(xml_geometry):
    geometry = []
    for xml_geom in xml_geometry:
        # Провера на multipolygon, т.к. функция from_gml() создаёт, но не заполняет Multipolygon
        if etree.QName(xml_geom).localname.lower().startswith('multi'):
            xml_polygons = [xml_polygon for xml_member in xml_geom for xml_polygon in xml_member]
        else:
            xml_polygons = [xml_geom]
        for xml_polygon in xml_polygons:
            fgeometry = {}
            for key, value in xml_polygon.attrib.items():
                fgeometry[key] = value
            fgeometry['geometry'] = etree.tostring(xml_polygon)
            geometry.append(fgeometry)
    return geometry


def find_attribute(request, attribute_name=str):
    xml_str = request.body.decode(request.encoding)
    root = etree.fromstring(xml_str)
    return root.attrib['version']
