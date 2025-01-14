from quart import Quart
from api.routes import routes


def create_app():
    """
    Creates and configures the Quart application.

    :return A Quart application instance.
    """
    app = Quart(__name__)

    # Register the routes blueprint
    app.register_blueprint(routes)
    return app
