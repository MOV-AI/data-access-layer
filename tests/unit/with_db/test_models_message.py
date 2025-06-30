class TestMessage:
    def test_export_portdata(self, models_message):
        models_message.export_portdata(db="local")
