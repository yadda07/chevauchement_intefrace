import sys
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QProgressBar, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette

class GeoProcessingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 400, 250)
        self.setWindowTitle('Interface de traitement géospatial')

        layout = QVBoxLayout()

        self.setStyleSheet('''
            QWidget {
                background-color: #282c34;
                color: #f0f0f0;
                font-size: 14px;
            }
            QLabel {
                padding: 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: #f0f0f0;
                border: none;
                padding: 10px 20px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLineEdit {
                background-color: #f0f0f0;
                color: #282c34;
                padding: 5px;
            }
            QProgressBar {
                border: 1px solid #f0f0f0;
                background-color: #f0f0f0;
                color: #282c34;
                height: 20px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        ''')

        self.setFont(QFont('Arial', 12))

        self.shapefile_label = QLabel('Chemin du Shapefile:')
        self.shapefile_path = QLabel('')
        self.select_shapefile_button = QPushButton('Sélectionner Shapefile')
        self.select_shapefile_button.clicked.connect(self.select_shapefile)

        self.save_dir_label = QLabel('Répertoire d\'enregistrement:')
        self.save_dir_path = QLabel('')
        self.select_save_dir_button = QPushButton('Sélectionner Répertoire')
        self.select_save_dir_button.clicked.connect(self.select_save_dir)

        self.percentage_label = QLabel('Pourcentage de chevauchement (0-100%):')
        self.percentage_input = QLineEdit('20')

        self.process_button = QPushButton('Traiter')
        self.process_button.clicked.connect(self.process_geometries)

        self.progress_bar = QProgressBar()

        layout.addWidget(self.shapefile_label)
        layout.addWidget(self.shapefile_path)
        layout.addWidget(self.select_shapefile_button)

        layout.addWidget(self.save_dir_label)
        layout.addWidget(self.save_dir_path)
        layout.addWidget(self.select_save_dir_button)

        layout.addWidget(self.percentage_label)
        layout.addWidget(self.percentage_input)

        layout.addWidget(self.process_button)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def select_shapefile(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, 'Sélectionner Shapefile', '', 'Shapefile (*.shp);;All Files (*)', options=options)
        if file_name:
            self.shapefile_path.setText(file_name)

    def select_save_dir(self):
        options = QFileDialog.Options()
        dir_name = QFileDialog.getExistingDirectory(self, 'Sélectionner Répertoire', options=options)
        if dir_name:
            self.save_dir_path.setText(dir_name)

    def process_geometries(self):
        shapefile_path = self.shapefile_path.text()
        save_dir = self.save_dir_path.text()
        percentage_overlap = float(self.percentage_input.text())

        gdf = gpd.read_file(shapefile_path)

        gdf = gdf[~gdf['geometry'].isna() & ~gdf['geometry'].is_empty]

        gdf['geometry'] = gdf['geometry'].buffer(0)

        gdf['area'] = gdf['geometry'].area

        sindex = gdf.sindex

        overlapping_rows = []

        total_geometries = len(gdf)
        processed_geometries = 0

        for index1, row1 in gdf.iterrows():
            possible_matches_index = list(sindex.intersection(row1['geometry'].bounds))
            possible_matches = gdf.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.intersects(row1['geometry'])]

            precise_matches = precise_matches[precise_matches.index != index1]

            for index2, row2 in precise_matches.iterrows():
                intersection = row1['geometry'].intersection(row2['geometry'])

                if intersection.geom_type == 'MultiPolygon':
                    for poly in intersection.geoms:
                        intersection_area = poly.area

                        if intersection_area / row1['area'] > percentage_overlap / 100.0:
                            print(f'Géométrie {index1} et géométrie {index2} se superposent de plus de {percentage_overlap}%.')
                            overlapping_rows.append(row1)
                elif intersection.geom_type == 'Polygon':
                    intersection_area = intersection.area

                    if intersection_area / row1['area'] > percentage_overlap / 100.0:
                        print(f'Géométrie {index1} et géométrie {index2} se superposent de plus de {percentage_overlap}%.')
                        overlapping_rows.append(row1)

            processed_geometries += 1
            self.progress_bar.setValue(int(processed_geometries * 100 / total_geometries))

        overlapping_gdf = gpd.GeoDataFrame(overlapping_rows)

        overlapping_gdf.to_file(f'{save_dir}/resultat_superpostion.shp')
        print('Traitement terminé. Résultats enregistrés dans le répertoire spécifié.')

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Set the dark mode theme
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    window = GeoProcessingApp()
    window.show()
    sys.exit(app.exec_())
