from .ats_analyzer import bp as ats_analyzer_bp
from .doc_analyzer import bp as doc_analyzer_bp
from .health import bp as health_bp
from .linux_helper import bp as linux_helper_bp
from .mac_helper import bp as mac_helper_bp
from .resume_builder import bp as resume_builder_bp
from .windows_helper import bp as windows_helper_bp
from .workflow_builder import bp as workflow_builder_bp


def register_blueprints(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(linux_helper_bp)
    app.register_blueprint(windows_helper_bp)
    app.register_blueprint(mac_helper_bp)
    app.register_blueprint(workflow_builder_bp)
    app.register_blueprint(doc_analyzer_bp)
    app.register_blueprint(ats_analyzer_bp)
    app.register_blueprint(resume_builder_bp)
