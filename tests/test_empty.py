import unittest


class TestDAL(unittest.TestCase):

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

    def test_empty(self):
        return True

    def test_imports(self):
        from dal import (
            api,
            backup,
            classes,
            data,
            helpers,
            models,
            movaidb,
            plugins,
            scopes,
            tools,
            validation
        )
        from dal.movaidb import MovaiDB
        from dal.scopes import scopes


if __name__ == "__main__":
    unittest.main()
