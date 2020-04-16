from mock import MagicMock
from unittest import TestCase
from evennia.sessions import sessionlinkhandler

from django.test import override_settings


class TestLinkSessionHandler(TestCase):

    def setUp(self):
        self.account = MagicMock()
        self.handler = sessionlinkhandler.SessionLinkHandler(self.account)

    def test_get(self):
        "Check get method"
        self.assertEqual(self.handler.get(), [])
        self.assertEqual(self.handler.get(100), [])

        s1 = MagicMock()
        s1.sessid = 1
        self.handler.do_add(s1)
        self.assertEqual([s.sessid for s in self.handler.get()], [s1.sessid])

        s2 = MagicMock()
        s2.sessid = 2
        self.handler.do_add(s2)
        self.assertEqual([s.uid for s in self.handler.get()], [s1.uid, s2.uid])
        self.assertEqual([s.sessid for s in self.handler.get()], [s1.sessid, s2.sessid])

    def test_all(self):
        "Check all method"
        self.assertEqual(self.handler.get(), self.handler.all())

    def test_count(self):
        "Check count method"
        self.assertEqual(self.handler.count(), len(self.handler.get()))


class TestAccountSessionHandler(TestCase):
    "Check AccountSessionHandler class"


    def test_before_link(self):
        """
        Just test to make sure we can add sessions to Accounts.
        """
        account = MagicMock()
        handler = sessionlinkhandler.AccountSessionHandler(account)
        session = MagicMock()
        account.db.FIRST_LOGIN = False
        handler.at_before_link_session(session)

        account.at_init.assert_called()
        account.at_first_login.assert_not_called()
        account.at_pre_login.assert_called()

    def test_before_link_first_login(self):
        """
        Test whether the First Login hook is being called.
        """
        account = MagicMock()
        account.db.FIRST_LOGIN = True
        handler = sessionlinkhandler.AccountSessionHandler(account)
        session = MagicMock()

        handler.at_before_link_session(session)

        account.at_first_login.assert_called()

    @override_settings(MULTISESSION_MODE=3)
    def test_before_link_multisession_plus(self):
        account = MagicMock()
        handler = sessionlinkhandler.AccountSessionHandler(account)
        session = MagicMock()

        handler.at_before_link_session(session)

        session.sessionhandler.disconnect_duplicate_sessions.assert_not_called()

    @override_settings(MULTISESSION_MODE=0)
    def test_before_link_multisession_0(self):
        """
        Test whether the Multisession mode 0 duplicate check is running.
        """
        account = MagicMock()
        handler = sessionlinkhandler.AccountSessionHandler(account)
        session = MagicMock()

        handler.at_before_link_session(session)

        session.sessionhandler.disconnect_duplicate_sessions.assert_called_with(session)

    @override_settings(CMDSET_SESSION="testing cmdset")
    def test_link_session(self):
        account = MagicMock()
        account.pk = 5
        account.username = "TestMan"
        handler = sessionlinkhandler.AccountSessionHandler(account)
        session = MagicMock()

        handler.at_link_session(session)

        self.assertEqual(account.pk, session.uid)
        self.assertEqual(account.username, session.uname)
        self.assertTrue(session.logged_in)
        self.assertEqual(session.cmdset_storage, "testing cmdset")

    def test_after_link_session(self):
        account = MagicMock()
        handler = sessionlinkhandler.AccountSessionHandler(account)
        session = MagicMock()
