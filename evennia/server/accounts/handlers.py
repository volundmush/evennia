from evennia.evlib.cmdsets.cmdhandler import CmdHandler


class AccountCmdHandler(CmdHandler):
    session = None

    def get_cmdobjects(self, session=None):
        cmdobjects = super().get_cmdobjects(session)
        cmdobjects['account'] = self.cmdobj
        return cmdobjects

