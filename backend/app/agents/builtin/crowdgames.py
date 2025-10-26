"""Агент для CrowdGames."""
from bs4 import BeautifulSoup
import re
from typing import AsyncGenerator
from ..base import HTMLAgent, Fetched, ListingEventDraft


class CrowdGamesAgent(HTMLAgent):
    """Агент для мониторинга каталога CrowdGames."""

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Извлечь события из HTML."""
        soup = BeautifulSoup(fetched.body, 'html.parser')

        # Ищем карточки товаров
        items = soup.select(self.selectors.get('item', '.product, .game-item, .collection-item'))

        for item in items:
            try:
                title_elem = item.select_one(self.selectors.get('title', '.product-title, .game-title, .title'))
                price_elem = item.select_one(self.selectors.get('price', '.price, .product-price'))
                url_elem = item.select_one(self.selectors.get('url', 'a'))
                badge_elem = item.select_one(self.selectors.get('badge', '.badge, .label, .status'))
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
                    elif any(word in badge_text for word in ['новинка', 'new', 'новое']):
                        kind = 'release'
                    elif any(word in badge_text for word in ['скидка', 'sale', 'акция', 'выгодно']):
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

                    # Ищем старую цену для расчета скидки
                    old_price_match = re.search(r'(\d[\d\s]*)\s*₽', price_text)
                    # Если есть зачеркнутая цена
                    old_price_elem = item.select_one('.old-price, .price-old')
                    if old_price_elem and price:
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
                    if any(word in availability_text for word in ['нет в наличии', 'закончилось', 'под заказ']):
                        in_stock = False

                yield ListingEventDraft(
                    title=title,
                    url=f"https://www.crowdgames.ru{url}" if url and not url.startswith('http') else url,
                    store_id='crowdgames',
                    kind=kind,
                    price=price,
                    discount_pct=discount_pct,
                    in_stock=in_stock
                )

            except Exception as e:
                print(f"Error parsing item: {e}")
                continue