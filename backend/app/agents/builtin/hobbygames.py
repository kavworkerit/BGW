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

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Извлечь события из HTML для каталога новинок."""
        soup = BeautifulSoup(fetched.body, 'html.parser')

        # Ищем карточки товаров
        items = soup.select(self.selectors.get('item', '.product-item, .product, .catalog-item'))

        for item in items:
            try:
                title_elem = item.select_one(self.selectors.get('title', '.product-item__title, .product-title, .title'))
                price_elem = item.select_one(self.selectors.get('price', '.product-item__price, .price'))
                url_elem = item.select_one(self.selectors.get('url', 'a.product-item__link, a'))
                badge_elem = item.select_one(self.selectors.get('badge', '.product-item__label, .badge, .label'))
                availability_elem = item.select_one(self.selectors.get('availability', '.stock, .availability'))
                edition_elem = item.select_one(self.selectors.get('edition', '.edition, .variant'))

                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = url_elem.get('href') if url_elem else None

                # Определяем тип события
                kind = 'release'  # по умолчанию для каталога новинок
                if badge_elem:
                    badge_text = badge_elem.get_text(strip=True).lower()
                    if any(word in badge_text for word in ['предзаказ', 'preorder', 'скоро']):
                        kind = 'preorder'
                    elif any(word in badge_text for word in ['новинка', 'new', 'поступление']):
                        kind = 'release'
                    elif any(word in badge_text for word in ['скидка', 'sale', 'акция', 'hit']):
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

                    # Ищем скидку в тексте
                    discount_match = re.search(r'-(\d+)%|скидка\s*(\d+)%', price_text)
                    if discount_match:
                        discount_pct = float(discount_match.group(1) or discount_match.group(2))

                # Проверяем старую цену
                old_price_elem = item.select_one('.old-price, .regular-price, .price-old')
                if old_price_elem and price and not discount_pct:
                    old_price_text = old_price_elem.get_text(strip=True)
                    old_price_match = re.search(r'(\d[\d\s]*)\s*₽', old_price_text)
                    if old_price_match:
                        old_price = float(old_price_match.group(1).replace(' ', ''))
                        if old_price > price:
                            discount_pct = round(((old_price - price) / old_price) * 100, 2)

                # Извлекаем издание/вариант
                edition = None
                if edition_elem:
                    edition = edition_elem.get_text(strip=True)
                elif badge_elem:
                    badge_text = badge_elem.get_text(strip=True)
                    # Некоторые издания указываются в бейдже
                    if any(word in badge_text.lower() for word in ['делюкс', 'deluxe', 'коллекционное', 'подарочное']):
                        edition = badge_text

                # Определяем наличие
                in_stock = True
                if availability_elem:
                    availability_text = availability_elem.get_text(strip=True).lower()
                    if any(word in availability_text for word in ['нет в наличии', 'закончилось', 'ожидается']):
                        in_stock = False

                yield ListingEventDraft(
                    title=title,
                    url=f"https://hobbygames.ru{url}" if url and not url.startswith('http') else url,
                    store_id='hobbygames_catalog_new',
                    kind=kind,
                    price=price,
                    discount_pct=discount_pct,
                    edition=edition,
                    in_stock=in_stock
                )

            except Exception as e:
                print(f"Error parsing catalog item: {e}")
                continue