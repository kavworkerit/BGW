"""Агент для Звезда."""
from bs4 import BeautifulSoup
import re
from typing import AsyncGenerator
from ..base import HTMLAgent, Fetched, ListingEventDraft


class ZvezdaAgent(HTMLAgent):
    """Агент для мониторинга каталога Звезда."""

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Извлечь события из HTML."""
        soup = BeautifulSoup(fetched.body, 'html.parser')

        # Ищем карточки товаров
        items = soup.select(self.selectors.get('item', '.product, .item, .catalog-item, .game-item'))

        for item in items:
            try:
                title_elem = item.select_one(self.selectors.get('title', '.product-title, .title, .name'))
                price_elem = item.select_one(self.selectors.get('price', '.price, .cost'))
                url_elem = item.select_one(self.selectors.get('url', 'a'))
                badge_elem = item.select_one(self.selectors.get('badge', '.badge, .label, .mark'))
                availability_elem = item.select_one(self.selectors.get('availability', '.stock, .available'))

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
                    elif any(word in badge_text for word in ['новинка', 'new', 'поступление']):
                        kind = 'release'
                    elif any(word in badge_text for word in ['скидка', 'sale', 'акция', 'спеццена']):
                        kind = 'discount'

                # Извлекаем цену
                price = None
                discount_pct = None
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Ищем цену
                    price_match = re.search(r'(\d[\d\s]*)\s*₽', price_text)
                    if price_match:
                        price = float(price_match.group(1).replace(' ', ''))

                    # Ищем процент скидки
                    discount_match = re.search(r'(\d+)%', price_text)
                    if discount_match:
                        discount_pct = float(discount_match.group(1))

                # Проверяем наличие старой цены
                old_price_elem = item.select_one('.old-price, .regular-price, .price-old')
                if old_price_elem and price and not discount_pct:
                    old_price_text = old_price_elem.get_text(strip=True)
                    old_price_match = re.search(r'(\d[\d\s]*)\s*₽', old_price_text)
                    if old_price_match:
                        old_price = float(old_price_match.group(1).replace(' ', ''))
                        if old_price > price:
                            discount_pct = round(((old_price - price) / old_price) * 100, 2)

                # Определяем наличие
                in_stock = True
                if availability_elem:
                    availability_text = availability_elem.get_text(strip=True).lower()
                    if any(word in availability_text for word in ['нет в наличии', 'закончилось', 'ожидается поступление']):
                        in_stock = False

                yield ListingEventDraft(
                    title=title,
                    url=f"https://zvezda.org.ru{url}" if url and not url.startswith('http') else url,
                    store_id='zvezda',
                    kind=kind,
                    price=price,
                    discount_pct=discount_pct,
                    in_stock=in_stock
                )

            except Exception as e:
                print(f"Error parsing item: {e}")
                continue