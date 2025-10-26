"""Агент для Лавки Игр."""
from bs4 import BeautifulSoup
import re
from typing import AsyncGenerator
from ..base import HTMLAgent, Fetched, ListingEventDraft


class LavkaIgrShopAgent(HTMLAgent):
    """Агент для мониторинга магазина Лавка Игр."""

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Извлечь события из HTML."""
        soup = BeautifulSoup(fetched.body, 'html.parser')

        # Ищем карточки товаров
        items = soup.select(self.selectors.get('item', '.product-card'))

        for item in items:
            try:
                title_elem = item.select_one(self.selectors.get('title', '.product-card__title'))
                price_elem = item.select_one(self.selectors.get('price', '.price'))
                url_elem = item.select_one(self.selectors.get('url', 'a.product-card__link'))
                badge_elem = item.select_one(self.selectors.get('badge', '.badge'))
                stock_elem = item.select_one(self.selectors.get('stock', '.stock-status'))

                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = url_elem.get('href') if url_elem else None

                # Определяем тип события
                kind = 'price'  # по умолчанию
                discount_pct = None

                if badge_elem:
                    badge_text = badge_elem.get_text(strip=True).lower()
                    if 'предзаказ' in badge_text or 'preorder' in badge_text:
                        kind = 'preorder'
                    elif 'новинка' in badge_text or 'new' in badge_text:
                        kind = 'release'
                    elif 'акция' in badge_text or 'скидка' in badge_text:
                        kind = 'discount'
                        # Ищем процент скидки
                        discount_match = re.search(r'(\d+)%', badge_text)
                        if discount_match:
                            discount_pct = float(discount_match.group(1))

                # Извлекаем цену
                price = None
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Убираем старую цену если есть
                    price_text = re.sub(r'\d+[\d\s]*₽.*?(\d+[\d\s]*₽)', r'\1', price_text)
                    price_match = re.search(r'(\d[\d\s]*)\s*₽', price_text)
                    if price_match:
                        price = float(price_match.group(1).replace(' ', ''))

                # Проверяем наличие
                in_stock = True
                if stock_elem:
                    stock_text = stock_elem.get_text(strip=True).lower()
                    in_stock = 'нет в наличии' not in stock_text and 'под заказ' not in stock_text

                yield ListingEventDraft(
                    title=title,
                    url=f"https://www.lavkaigr.ru{url}" if url and not url.startswith('http') else url,
                    store_id='lavkaigr',
                    kind=kind,
                    price=price,
                    discount_pct=discount_pct,
                    in_stock=in_stock
                )

            except Exception as e:
                print(f"Error parsing item: {e}")
                continue


class LavkaIgrProjectsAgent(LavkaIgrShopAgent):
    """Агент для мониторинга проектов Лавка Игр."""
    pass