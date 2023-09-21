from django.test import SimpleTestCase
from django.urls import reverse, resolve

from ..views import HomeView, black_list_view, moderator_list_view, BannedListView, unban_user_ajax_view, \
    get_chat_banned_info_ajax_view, get_banned_admin_info_ajax_view, chat_room_view


class TestUrls(SimpleTestCase):
    def test_home_url_resolves(self):
        url = reverse('chat:home')
        self.assertEqual(resolve(url).func.view_class, HomeView)

    def test_chat_room_url_resolves(self):
        url = reverse('chat:chat-room', kwargs={'chat_owner_slug': 'some-slug'})
        self.assertEqual(resolve(url).func, chat_room_view)

    def test_black_list_url_resolves(self):
        url = reverse('chat:black-list')
        self.assertEqual(resolve(url).func, black_list_view)

    def test_moderators_url_resolves(self):
        url = reverse('chat:moder-list')
        self.assertEqual(resolve(url).func, moderator_list_view)

    def test_banned_users_url_resolves(self):
        url = reverse('chat:banned-list')
        self.assertEqual(resolve(url).func.view_class, BannedListView)

    def test_ajax_unban_url_resolves(self):
        url = reverse('chat:ajax-unban-user')
        self.assertEqual(resolve(url).func, unban_user_ajax_view)

    def test_ajax_banned_list_url_resolves(self):
        url = reverse('chat:ajax-banned-list')
        self.assertEqual(resolve(url).func, get_chat_banned_info_ajax_view)

    def test_ajax_banned_search_admin_url_resolves(self):
        url = reverse('chat:ajax-search-admin-banned-list')
        self.assertEqual(resolve(url).func, get_banned_admin_info_ajax_view)
