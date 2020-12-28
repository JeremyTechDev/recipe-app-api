from unittest.mock import patch
from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import TestCase

PATCH_ADDRESS = 'django.db.utils.ConnectionHandler.__getitem__'


class TestCommands(TestCase):

    def test_wait_for_db_ready(self):
        """Tests waiting for db when db is available"""

        with patch(PATCH_ADDRESS) as mock_getitem:
            mock_getitem.return_value = True
            call_command('wait_for_db')

        self.assertEqual(mock_getitem.call_count, 1)

    @patch('time.sleep', return_value=True)
    def test_wait_for_db(self, mock_time_sleep):
        """Test waiting for db to start"""

        with patch(PATCH_ADDRESS) as mock_getitem:
            # Raises OperationError 5 times, then returns True
            mock_getitem.side_effect = [OperationalError] * 5 + [True]
            call_command('wait_for_db')
            self.assertEqual(mock_getitem.call_count, 6)
