import os

from PyQt5.QtCore import QVariant

from qgis.core import (
    QgsFeature,
    QgsField,
    QgsMarkerSymbol,
    QgsProject,
    QgsRasterLayer,
    QgsSingleSymbolRenderer,
    QgsVectorFileWriter,
    QgsVectorLayer,
)

# =====================================================
# ROOT FOLDER (SEARCHES ALL SUBDIRECTORIES)
# =====================================================
# SOURCED FROM https://github.com/generalpiston/geojson-us-city-boundaries
root_folder = (
    r"C:\TEMP\geojson-us-city-boundaries\cities"
)

# =====================================================
# OUTPUT FILES
# =====================================================

output_gpkg = (
    r"C:\TEMP\springfield_features.gpkg"
)

output_layer_name = "Springfield_Cities"

# =====================================================
# CREATE MEMORY LAYER
# =====================================================

memory_layer = QgsVectorLayer(
    "Point?crs=EPSG:4326",
    output_layer_name,
    "memory",
)

provider = memory_layer.dataProvider()

fields_added = False
total_added = 0

# =====================================================
# RECURSIVELY WALK THROUGH ALL DIRECTORIES
# =====================================================

for current_dir, subdirs, files in os.walk(root_folder):

    for filename in files:

        # Only process Springfield GeoJSON files
        if filename.lower() == "springfield.json":

            file_path = os.path.join(current_dir, filename)

            # Get state name from parent directory
            state_name = os.path.basename(current_dir).upper()

            print(f"Processing: {file_path} ({state_name})")

            # =================================================
            # LOAD GEOJSON LAYER
            # =================================================

            layer = QgsVectorLayer(
                file_path,
                filename,
                "ogr",
            )

            if not layer.isValid():
                print("  -> Failed to load")
                continue

            # =================================================
            # COPY FIELD STRUCTURE ONCE
            # =================================================

            if not fields_added:

                provider.addAttributes(layer.fields())

                # Add custom STATE_NAME field
                provider.addAttributes([
                    QgsField(
                        "STATE_NAME",
                        QVariant.String,
                    )
                ])

                memory_layer.updateFields()

                fields_added = True

            # =================================================
            # FIND SPRINGFIELD FEATURES
            # =================================================

            for feature in layer.getFeatures():

                name_value = feature["NAME"]

                if (
                    name_value is not None
                    and str(name_value).strip().lower()
                    == "springfield"
                ):

                    new_feature = QgsFeature(
                        memory_layer.fields()
                    )

                    # Convert polygon to centroid point
                    centroid = feature.geometry().centroid()

                    new_feature.setGeometry(centroid)

                    # Copy existing attributes
                    attrs = feature.attributes()

                    # Add STATE_NAME attribute
                    attrs.append(state_name)

                    # Apply attributes
                    new_feature.setAttributes(attrs)

                    # Add feature to layer
                    provider.addFeature(new_feature)

                    total_added += 1

                    print(
                        f"  -> Added Springfield "
                        f"({state_name})"
                    )

# =====================================================
# ADD OPENSTREETMAP BASEMAP
# =====================================================

url = (
    "type=xyz&url="
    "https://tile.openstreetmap.org/"
    "{z}/{x}/{y}.png"
)

osm = QgsRasterLayer(
    url,
    "OpenStreetMap",
    "wms",
)

QgsProject.instance().addMapLayer(osm)

# =====================================================
# FINALIZE MEMORY LAYER
# =====================================================

memory_layer.updateExtents()

# =====================================================
# STYLE THE LAYER
# =====================================================

symbol = QgsMarkerSymbol.createSimple({
    "name": "circle",
    "color": "255,0,0,255",
    "outline_color": "255,255,255,255",
    "outline_width": "0.8",
    "size": "5",
})

memory_layer.setRenderer(
    QgsSingleSymbolRenderer(symbol)
)

memory_layer.triggerRepaint()

# =====================================================
# ADD LAYER TO QGIS PROJECT
# =====================================================

QgsProject.instance().addMapLayer(memory_layer)

# =====================================================
# SAVE AS PERMANENT GEOPACKAGE
# =====================================================

options = QgsVectorFileWriter.SaveVectorOptions()

options.driverName = "GPKG"
options.layerName = output_layer_name

QgsVectorFileWriter.writeAsVectorFormatV3(
    memory_layer,
    output_gpkg,
    QgsProject.instance().transformContext(),
    options,
)

# =====================================================
# SUMMARY
# =====================================================

print("\n===================================")
print("PERMANENT LAYER SAVED")
print(output_gpkg)
print(f"Total Springfield features: {total_added}")
print("===================================")
