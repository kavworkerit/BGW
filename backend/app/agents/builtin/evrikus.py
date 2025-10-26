"""Агент для Evrikus."""
from bs4 import BeautifulSoup
import re
from typing import AsyncGenerator
from ..base import HTMLAgent, Fetched, ListingEventDraft


class EvrikusCatalogAgent(HTMLAgent):
    """Агент для мониторинга каталога Evrikus."""

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Извлечь события из HTML."""
        soup = BeautifulSoup(fetched.body, 'html.parser')

        # Ищем карточки товаров
        items = soup.select(self.selectors.get('item', '.product-card, .product-item, .item'))

        for item in items:
            try:
                title_elem = item.select_one(self.selectors.get('title', '.product-title, .title, .name'))
                price_elem = item.select_one(self.selectors.get('price', '.price, .product-price'))
                url_elem = item.select_one(self.selectors.get('url', 'a'))
                badge_elem = item.select_one(self.selectors.get('badge', '.badge, .label, .tag'))
                availability_elem = item.select_one(self.selectors.get('availability', '.stock, .availability'))

                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = url_elem.get('href') if url_elem else None

                # Определяем тип события
                kind = 'price'  # по умолчанию
                if badge_elem:
                    badge_text = badge_elem.get_text(strip=True).lower()
                    if any(word in badge_text for word in ['предзаказ', 'preorder', 'скоро']):
                        kind = 'preorder'
                    elif any(word in badge_text for word in ['новинка', 'new', 'новый']):
                        kind = 'release'
                    elif any(word in badge_text for word in ['скидка', 'sale', '-%', 'акция']):
                        kind = 'discount'

                # Извлекаем цену
                price = None
                discount_pct = None
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Ищем цену в различных форматах
                    price_match = re.search(r'(\d[\d\s]*)\s*₽', price_text)
                    if price_match:
                        price = float(price_match.group(1).replace(' ', ''))

                    # Ищем процент скидки
                    discount_match = re.search(r'(\d+)%', price_text)
                    if discount_match:
                        discount_pct = float(discount_match.group(1))

                # Определяем наличие
                in_stock = True
                if availability_elem:
                    availability_text = availability_elem.get_text(strip=True).lower()
                    if any(word in availability_text for word in ['нет в наличии', 'под заказ', 'закончился']):
                        in_stock = False

                yield ListingEventDraft(
                    title=title,
                    url=f"https://evrikus.ru{url}" if url and not url.startswith('http') else url,
                    store_id='evrikus',
                    kind=kind,
                    price=price,
                    discount_pct=discount_pct,
                    in_stock=in_stock
                )

            except Exception as e:
                print(f"Error parsing item: {e}")
                continue