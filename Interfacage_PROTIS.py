from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QFont
from serial import Serial, SerialException
import pyqtgraph as pg
import pyqtgraph.exporters
import random
import numpy as np

class Data(QtCore.QObject):
    # On associe à data_generated un signal PyQt
    data_generated = QtCore.pyqtSignal(float)  # Signal pour transmettre les valeurs

    def __init__(self, use_serial=True):
        super().__init__()
        self.running = False
        self.use_serial = use_serial  # Permet de choisir entre Nucleo et mode test
        self.serial_port = None
        self.counter = 0
        self.elapsed_time = 0  # Compteur pour suivre le temps écoulé

        if self.use_serial:
            try:
                self.serial_port = Serial('/dev/cu.usbmodem11103', 115200, timeout=1)
                print("Connexion série établie avec la carte Nucleo")
            except SerialException:
                print("Impossible de se connecter à la carte Nucleo, passage en mode test")
                self.use_serial = False

    def start_stop_generation(self):
        """Démarre ou arrête l'acquisition des données"""
        self.running = not self.running

    def generate_data(self):
        """Récupère les données depuis la Nucleo ou génère des valeurs aléatoires"""
        if self.running:
            if self.use_serial and self.serial_port:
                self.serial_port.write(b'A')  # Envoi de la commande 'A' à la Nucleo
                try:
                    rec_data_nucleo = self.serial_port.readline().decode().strip()
                    if rec_data_nucleo:
                        value = float(rec_data_nucleo)
                        tension = value * 3.3
                        self.data_generated.emit(tension)
                        self.counter += 1  # Génération aléatoire en mode test
                except (ValueError, SerialException):
                    print("Erreur de lecture série")
            else:
                value = random.uniform(0, 10)
                self.counter += 1  # Génération aléatoire en mode test
                self.data_generated.emit(value)

            # Incrémente le temps écoulé
            self.elapsed_time += self.parent().timer.interval()
            # Vérifie si le temps écoulé a atteint stop_after_time
            if self.elapsed_time >= self.parent().stop_after_time:
                if self.parent().flag:
                    self.running = False
                    self.parent().timer.stop()
                    self.parent().button_start.setText("Start Acquisition")
                    self.elapsed_time = 0  # Réinitialise le compteur de temps écoulé

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.graphical_elements_class = Graphical_elements()
        self.Data_class = Data()

        self.use_serial = True  # Défaut : utiliser la Nucleo si disponible
        self.flag = False
        self.class_Data = Data(use_serial=self.use_serial)
        self.class_Data.setParent(self)  # Associe l'instance de Data à MainWindow
        self.class_Data.data_generated.connect(self.update_plot)  # À chaque fois qu'un signal est détécté, on update le plot

        self.stop_after_time = 10000  # Durée après laquelle le timer doit s'arrêter (en ms)

        ##== Cosmétiques ici ==##

        # Graphique
        self.plot_graph = pg.PlotWidget()
        self.plot_graph.setBackground("w")
        self.plot_graph.setLabel("left", "Valeur de la mesure")
        self.plot_graph.setLabel("bottom", "Temps (x100 ms)")
        self.plot_graph.setTitle("Acquisition des mesures de la carte Nucléo")

        self.curve = self.plot_graph.plot([], [], pen=pg.mkPen(color=(255, 0, 0)), name='Points de coïncidences', symbol="+", symbolSize=15, symbolBrush="b",)

        # Boutons
        self.button_start = QtWidgets.QPushButton('Start Acquisition', self)
        self.button_start.clicked.connect(self.toggle_generation)

        self.button_mode = QtWidgets.QPushButton('Mode: Nucleo', self)
        self.button_mode.clicked.connect(self.toggle_mode)

        self.button_export = QtWidgets.QPushButton("Exporter l'image", self)
        self.button_export.clicked.connect(self.export_plots)

        self.button_temps_int = QtWidgets.QPushButton('Integration Time', self)
        self.button_temps_int.clicked.connect(self.input_time)

        self.button_temps_int2 = QtWidgets.QPushButton('Total Time', self)
        self.button_temps_int2.clicked.connect(self.input_time_2)

        self.reinitialiser = QtWidgets.QPushButton('Réinitialiser', self)
        self.reinitialiser.clicked.connect(self.reboot)

        # Labels
        self.counter_label = QtWidgets.QLabel('Nombres de points:')
        self.time_integration_label = QtWidgets.QLabel("Période d'intégration:")
        self.duree_total = QtWidgets.QLabel("Temps d'intégration:")

        #Check Box
        self.check_duree = QtWidgets.QCheckBox('Test')
        self.check_duree.stateChanged.connect(self.yes_no)

        # Textes
        self.titre_1 = QtWidgets.QLabel('Tracé du nombre de coincidences détéctées')
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(16)
        self.titre_1.setFont(font)
        self.titre_1.setAlignment(QtCore.Qt.AlignCenter)

        self.sous_titre_1 = QtWidgets.QLabel('Fonctionnalités')
        font_sous_titre = QtGui.QFont()
        font_sous_titre.setBold(True)
        font_sous_titre.setPointSize(12)
        self.sous_titre_1.setFont(font_sous_titre)

        top_layout = QtWidgets.QVBoxLayout()
        top_layout.addWidget(self.titre_1)
        top_layout.addWidget(self.graphical_elements_class.line)
        top_layout.addWidget(self.plot_graph)
        top_layout.addWidget(self.graphical_elements_class.line)

        # Layout vertical pour la colonne de gauche
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(self.sous_titre_1)
        left_layout.addWidget(self.button_mode)
        left_layout.addWidget(self.button_start)
        left_layout.addWidget(self.button_export)
        left_layout.addWidget(self.button_temps_int)
        left_layout.addWidget(self.button_temps_int2)
        left_layout.addWidget(self.reinitialiser)
        left_layout.addWidget(self.check_duree)

        # Layout vertical pour la colonne de droite
        right_layout = QtWidgets.QVBoxLayout()
        self.data_label = QtWidgets.QLabel('Données supplémentaires')
        font_data = QtGui.QFont()
        font_data.setBold(True)
        font_data.setPointSize(12)
        self.data_label.setFont(font_data)
        right_layout.addWidget(self.data_label)
        right_layout.addWidget(self.counter_label)
        right_layout.addWidget(self.time_integration_label)
        right_layout.addWidget(self.duree_total)

        # Layout horizontal pour organiser les colonnes côte à côte
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        top_layout.addLayout(main_layout)

        container = QtWidgets.QWidget()
        container.setLayout(top_layout)
        self.setCentralWidget(container)

        ##== Définitions des fonctions utiles ==##

        # Timer pour mise à jour régulière
        self.interval = 100
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.class_Data.generate_data)
        self.timer.start(self.interval)  # Mise à jour toutes les 100 ms

        self.data_buffer = []

    def toggle_generation(self):
        """Démarre ou arrête l'acquisition"""
        self.class_Data.start_stop_generation()
        self.button_start.setText("Stop Acquisition" if self.class_Data.running else "Start Acquisition")
        if self.class_Data.running:
            self.class_Data.elapsed_time = 0  # Réinitialise le compteur de temps écoulé
            self.timer.setInterval(self.interval)
            self.timer.start(self.interval)

    def toggle_mode(self):
        """Bascule entre le mode Nucleo et le mode simulation"""
        self.use_serial = not self.use_serial
        self.class_Data = Data(use_serial=self.use_serial)
        self.class_Data.setParent(self)  # Associe l'instance de Data à MainWindow
        self.class_Data.data_generated.connect(self.update_plot)

        self.button_mode.setText("Mode: Nucleo" if self.use_serial else "Mode: Simulation")

    def update_plot(self, value):
        """Met à jour le graphique et le compteur de points"""
        self.data_buffer.append(value)
        self.curve.setData(range(len(self.data_buffer)), self.data_buffer)
        self.counter_label.setText(f'Nombres de points: {self.class_Data.counter}')

    def export_plots(self):
        exporter = pg.exporters.ImageExporter(self.plot_graph.plotItem)
        # save to file
        exporter.export('Graph_coincidences.png')

    def input_time(self):
        val, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Enter time interval (ms):')
        if ok:
            try:
                self.interval = int(val)
                if self.interval > 0:
                    self.timer.setInterval(self.interval)
                    self.time_integration_label.setText(f"Période d'intégration: {self.interval} ms")
                else:
                    QtWidgets.QMessageBox.warning(self, 'Invalid Input', 'Please enter a positive integer.')
            except ValueError:
                QtWidgets.QMessageBox.warning(self, 'Invalid Input', 'Please enter a valid integer.')
    
    def input_time_2(self):
        val, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Enter time interval (ms):')
        if ok:
            try:
                interval = int(val)
                self.stop_after_time = interval  # Durée après laquelle le timer doit s'arrêter (en ms)
                if interval > 0:
                    self.duree_total.setText(f"Temps total: {interval} ms")
                else:
                    QtWidgets.QMessageBox.warning(self, 'Invalid Input', 'Please enter a positive integer.')
            except ValueError:
                QtWidgets.QMessageBox.warning(self, 'Invalid Input', 'Please enter a valid integer.')
    
    def yes_no(self):
        self.flag = not self.flag

    def reboot(self):
        self.data_buffer = []

class Graphical_elements():
    def __init__(self):
        self.line = QtWidgets.QFrame()
        self.line.setFrameShape(QtWidgets.QFrame.HLine)  # Définir une ligne horizontale
        #self.line.setFrameShadow(QtWidgets.QFrame.Raised)  # Effet visuel
        self.line.setFixedHeight(2)  # Épaisseur de la ligne

# Lancer l'application
app = QtWidgets.QApplication([])
main = MainWindow()
main.show()
app.exec()
