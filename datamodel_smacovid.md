# SMACovid

## Description

This data model specifies the entities, and its relations, for a NGSI-LD system to monitor Hospital workers/patients. 

## Data Model

A Schema corresponding to this data model can be found at https://github.com/rui-vp-fernandes/models/edit/master/


-   `id` : Unique identifier. It shall be a URN in the form
    `urn:ngsi-ld:Smacovid:<identifier>` where `<identifier>` shall be a
    unique ID string.

-   `type` : Entity type. It must be equal to Smacovid.

-   `modifiedAt` or `dateModified` (NGSIv2): Last update timestamp of this
    entity.

    -   Attribute type: Property. [DateTime](https://schema.org/DateTime)
    -   Read-Only. Automatically generated.

-   `createdAt` or `dateCreated` (NGSIv2): Entity's creation timestamp.

    -   Attribute type: Property. [DateTime](https://schema.org/DateTime)
    -   Read-Only. Automatically generated.

-   `owner` : Entity's owners.

    -   Attribute type: `Relationship`. List of references to
        [Person](http://schema.org/Person) or
        [Organization](https://schema.org/Organization).
    -   Optional

{{Location and address are two typical attributes that are added here for convenience}}

-   `location` : Location of {{Entity Type}} represented by a GeoJSON geometry.

    -   Attribute type: `GeoProperty` or `geo:json` (NGSIv2).
    -   Normative References:
        [https://tools.ietf.org/html/rfc7946](https://tools.ietf.org/html/rfc7946)
    -   Mandatory if `address` is not defined.

-   `address` : Civic address of {{Entity Type}}

    -   Attribute type: `Property`
    -   Normative References:
        [https://schema.org/address](https://schema.org/address)
    -   Mandatory if `location` is not present.

{{Below there is a description of a typical attribute of type `Property`}}

-   `{{attributeName}}` : {{Description of the Attribute}}

    -   Normative References: {{Add a normative reference}}
    -   Attribute type: `Property`. {{Add here the attribute data type}}
    -   Attribute metadata Properties:
        -   `{{metadata Property name}}` : {{Metadata Property Description}}
    -   {{Optional/Mandatory}}

{Below there is a description of a typical attribute of type `Relationship`}}

-   `{{attributeName}}` : {{Description of the Attribute}}

    -   Normative References: {{Add a normative reference}}
    -   Attribute type: `Relationship`.
        {{Add here the description of the target relationship object}}
    -   Attribute metadata Properties:
        -   `{{metadata Property name}}` : {{Metadata Property Description}}
    -   {{Optional/Mandatory}}

**Note**: JSON Schemas are intended to capture the data type and associated
constraints of the different Attributes, regardless their final representation
format in NGSI(v2, LD).

## Examples of use

### Normalized Example

Normalized NGSI response

{{Provide a JSON example in NGSIv2 Normalized Format}}

### key-value pairs Example

Sample uses simplified representation for data consumers `?options=keyValues`

{{Provide a JSON example in NGSIv2 keyValues Format}}

### LD Example

Sample uses the NGSI-LD representation

{{Provide a JSON example in NGSI-LD Format}}

## Use it with a real service

{{Provide a link to a real service providing data following the harmonized data format}}

## Open Issues

{{Describe here any open issue}}
