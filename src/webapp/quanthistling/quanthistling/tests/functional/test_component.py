from quanthistling.tests import *

class TestComponentController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='component', action='index'))
        # Test response...
