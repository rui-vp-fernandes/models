# Parking

**Note: The latest version of these Data Models can be found at
[https://github.com/smart-data-models/dataModel.Parking](https://github.com/smart-data-models/dataModel.Parking)**

This repository is going to be archived (Jan-2020) and subsequent works will be carried out in [Smart data models] (https://github.com/smart-data-models) repositories. Further questions on migration. alberto.abella@fiware.org


This folder contains all the code that allows to expose harmonized datasets for
parking information. Those datasets follow the
[proposed smart parking data models](https://docs.google.com/document/d/17leIlKCE5EdOtrAurbIsvbjRnE6UMEXQcNVswvS0J_A/edit?usp=sharing).

Two different entity types are exposed:

-   `StreetParking`.- It represents an area, in a street, which can contain one
    or more parking spots.
-   `ParkingLot` .- It represents a public parking lot (underground or surface)
    with well defined entrance and exit points.

Parking data offered come from two different sources:

-   The city of Porto and the [OST platform](http://ost.pt).
-   The city of Santander ([SmartSantander Project](http://smartsantander.eu/)).

All the datasets exposed here are subject to the license claim made by the
original data sources. Please check carefully before using them.
