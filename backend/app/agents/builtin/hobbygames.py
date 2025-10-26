"""Агент для Hobby Games."""
from bs4 import BeautifulSoup
import re
from typing import AsyncGenerator
from ..base import HTMLAgent, Fetched, ListingEventDraft


class HobbyGamesComingSoonAgent(HTMLAgent):
    """Агент для мониторинга раздела Coming Soon на Hobby Games."""

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Извлечь события из HTML."""
        soup = BeautifulSoup(fetched.body, 'html.parser')

        # Ищем карточки товаров
        items = soup.select(self.selectors.get('item', '.product-item'))

        for item in items:
            try:
                title_elem = item.select_one(self.selectors.get('title', '.product-item__title'))
                price_elem = item.select_one(self.selectors.get('price', '.product-item__price'))
                url_elem = item.select_one(self.selectors.get('url', 'a.product-item__link'))
                badge_elem = item.select_one(self.selectors.get('badge', '.product-item__label'))

                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = url_elem.get('href') if url_elem else None

                # Определяем тип события
                kind = 'announce'  # по умолчанию
                if badge_elem:
                    badge_text = badge_elem.get_text(strip=True).lower()
                    if 'предзаказ' in badge_text or 'preorder' in badge_text:
                        kind = 'preorder'
                    elif 'новинка' in badge_text or 'new' in badge_text:
                        kind = 'release'

                # Извлекаем цену
                price = None
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r'(\d[\d\s]*)\s*₽', price_text)
                    if price_match:
                        price = float(price_match.group(1).replace(' ', ''))

                yield ListingEventDraft(
                    title=title,
                    url=f"https://hobbygames.ru{url}" if url and not url.startswith('http') else url,
                    store_id='hobbygames',
                    kind=kind,
                    price=price,
                    in_stock=True  # Предзаказ считается как в наличии
                )

            except Exception as e:
                print(f"Error parsing item: {e}")
                continue


class HobbyGamesCatalogNewAgent(HobbyGamesComingSoonAgent):
    """Агент для мониторинга раздела Catalog New на Hobby Games."""
    pass