from activities.views import systemlogActivity


def startup():
    try:
        systemlogActivity(
            action="Cow server restarted/reloaded (all ongoing sessions terminated).",
            arguments={})
    except:
        print("Startup logging error: No database available yet.")
        pass


startup()
