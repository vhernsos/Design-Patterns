import threading


class ConfiguracionGlobal:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def _initialize_from_db(self):
        from web.models import GlobalConfig                             
        config = GlobalConfig.load()
        self.moneda               = config.moneda
        self.porcentaje_impuestos = float(config.porcentaje_impuestos)
        self.limite_asistentes    = config.limite_asistentes
        self.notificaciones_activas = config.notificaciones_activas
        self.modo_mantenimiento   = config.modo_mantenimiento
        self._initialized = True

    def refresh(self):
        self._initialize_from_db()

    def get_moneda(self):
        if not self._initialized:
            self._initialize_from_db()
        return self.moneda

    def get_porcentaje_impuestos(self):
        if not self._initialized:
            self._initialize_from_db()
        return self.porcentaje_impuestos

    def get_limite_asistentes(self):
        if not self._initialized:
            self._initialize_from_db()
        return self.limite_asistentes

    def get_notificaciones_activas(self):
        if not self._initialized:
            self._initialize_from_db()
        return self.notificaciones_activas

    def get_modo_mantenimiento(self):
        if not self._initialized:
            self._initialize_from_db()
        return self.modo_mantenimiento

    def save_to_db(self, moneda=None, porcentaje_impuestos=None,
                   limite_asistentes=None, notificaciones_activas=None,
                   modo_mantenimiento=None):
        from web.models import GlobalConfig                             
        config = GlobalConfig.load()
        if moneda                is not None: config.moneda               = moneda
        if porcentaje_impuestos  is not None: config.porcentaje_impuestos = porcentaje_impuestos
        if limite_asistentes     is not None: config.limite_asistentes    = limite_asistentes
        if notificaciones_activas is not None: config.notificaciones_activas = notificaciones_activas
        if modo_mantenimiento    is not None: config.modo_mantenimiento   = modo_mantenimiento
        config.save()
        self.refresh()

    def __str__(self):
        return (
            f"ConfiguracionGlobal("
            f"moneda={self.get_moneda()}, "
            f"impuestos={self.get_porcentaje_impuestos()}%, "
            f"limite={self.get_limite_asistentes()}, "
            f"notificaciones={self.get_notificaciones_activas()}, "
            f"mantenimiento={self.get_modo_mantenimiento()})"
        )