class LocaleManager:
    def __init__(self):
        # Dictionary of all game text
        self.languages = {
            "en": {  # English (Original)
                "title": "EARTH INVADERS",
                "start": "DEFEND EARTH",
                "quit": "ABANDON MISSION",
                "score": "SCORE: ",
                "level": "LEVEL: ",
                "high_score": "BEST: ",
                "paused": "CEASEFIRE",
                "return_to_main": "PRESS Q TO ABANDON MISSION",
                "resume": "PRESS ESC TO RESUME",
                "game_over": "EARTH HAS FALLEN",
                "restart": "PRESS R TO RESTART",
                "lives": "LIVES: ",
                "proximity_warning": "!!! ENEMY PROXIMITY !!!",
                "proximity_alert": "BREACH IMMINENT",
                "ufo_alert": "UFO DETECTED!"
            },
            "la": {  # Latin (High Military Style)
                "title": "INVĀSŌRĒS TERRAE",
                "start": "TERRAM DĒFENDE",
                "quit": "MŪNUS RELINQUERE",
                "score": "PŪNCTA: ",
                "level": "GRADUS: ",
                "high_score": "OPTIMA: ",
                "paused": "INDŪTIAE",
                "return_to_main": "PRIMATŪ Q MŪNUS RELINQUERE",
                "resume": "PRIMATŪ ESC REDINTEGRĀ",
                "game_over": "TERRA CAPTA EST",
                "restart": "PRIMATŪ R DENUŌ INCIPE",
                "lives": "VĪTAE: ",
                "proximity_warning": "!!! HOSTIS PROPINQUUS !!!",
                "proximity_alert": "IRRUPTIŌ INSTANS",
                "ufo_alert": "UFO APPARUIT!"
            },
            "es": {  # Spanish
                "title": "INVASORES DE LA TIERRA",
                "start": "DEFIENDE LA TIERRA",
                "quit": "ABANDONAR MISIÓN",
                "score": "PUNTOS: ",
                "level": "NIVEL: ",
                "high_score": "RÉCORD: ",
                "paused": "ALTO EL FUEGO",
                "return_to_main": "PULSA Q PARA ABANDONAR MISIÓN",
                "resume": "PULSA ESC PARA REANUDAR",
                "game_over": "LA TIERRA HA CAÍDO",
                "restart": "PULSA R PARA REINTENTAR",
                "lives": "VIDAS: ",
                "proximity_warning": "!!! ENEMIGO CERCA !!!",
                "proximity_alert": "BRECHA INMINENTE",
                "ufo_alert": "¡UFO DETECTADO!"
            },
            "fr": {  # French
                "title": "ENVAHISSEURS DE LA TERRE",
                "start": "DÉFENDEZ LA TERRE",
                "quit": "ABANDONNER LA MISSION",
                "score": "SCORE: ",
                "level": "NIVEAU: ",
                "high_score": "MEILLEUR: ",
                "paused": "CESSEZ-LE-FEU",
                "return_to_main": "APPUYEZ SUR Q POUR ABANDONNER",
                "resume": "APPUYEZ SUR ESC POUR REPRENDRE",
                "game_over": "LA TERRE EST TOMBÉE",
                "restart": "APPUYEZ SUR R POUR RECOMMENCER",
                "lives": "VIES: ",
                "proximity_warning": "!!! ENNEMI À PROXIMITÉ !!!",
                "proximity_alert": "BRÈCHE IMMINENTE",
                "ufo_alert": "UFO DÉTECTÉ !"
            },
            "de": {  # German
                "title": "INVASOREN DER ERDE",
                "start": "VERTEIDIGE DIE ERDE",
                "quit": "MISSION ABBRECHEN",
                "score": "PUNKTE: ",
                "level": "LEVEL: ",
                "high_score": "REKORD: ",
                "paused": "WAFFENRUHE",
                "return_to_main": "Q ZUM ABBRECHEN DRÜCKEN",
                "resume": "ESC ZUM FORTSETZEN DRÜCKEN",
                "game_over": "DIE ERDE IST GEFALLEN",
                "restart": "R ZUM NEUSTART DRÜCKEN",
                "lives": "LEBEN: ",
                "proximity_warning": "!!! FEINDNÄHE !!!",
                "proximity_alert": "DURCHBRUCH STEHT BEVOR",
                "ufo_alert": "UFO GESICHTET!"
            }
        }

        self.lang_codes = list(self.languages.keys())
        self.current_index = 0
        self.current_lang = self.lang_codes[self.current_index]

    def get(self, key):
        """Retrieves the string for the current language."""
        return self.languages[self.current_lang].get(key, key)

    def toggle_language(self):
        """Cycles to the next language in the dictionary."""
        self.current_index = (self.current_index + 1) % len(self.lang_codes)
        self.current_lang = self.lang_codes[self.current_index]
        return self.current_lang