"""Агент для Nastol.io."""
from bs4 import BeautifulSoup
import re
from typing import AsyncGenerator
from ..base import HTMLAgent, Fetched, ListingEventDraft


class NastolPublicationsAgent(HTMLAgent):
    """Агент для мониторинга публикаций Nastol.io."""

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Извлечь события из HTML."""
        soup = BeautifulSoup(fetched.body, 'html.parser')

        # Ищем карточки постов
        items = soup.select(self.selectors.get('item', '.post-card, .article-item, .post'))

        for item in items:
            try:
                title_elem = item.select_one(self.selectors.get('title', '.post-card__title, .title, h2, h3'))
                date_elem = item.select_one(self.selectors.get('date', 'time[datetime], .date, .post-date'))
                url_elem = item.select_one(self.selectors.get('url', 'a'))
                category_elem = item.select_one(self.selectors.get('category', '.category, .tag'))

                if not title_elem or not url_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = url_elem.get('href')

                # Получаем текст поста для анализа
                content_elem = item.select_one('.post-card__excerpt, .excerpt, .summary')
                content = content_elem.get_text(strip=True) if content_elem else ''
                full_content = f"{title} {content}".lower()

                # Добавляем категорию в анализ
                category = ''
                if category_elem:
                    category = category_elem.get_text(strip=True).lower()
                    full_content += f" {category}"

                # Определяем тип события по ключевым словам
                kind = 'announce'  # по умолчанию
                if any(word in full_content for word in ['предзаказ', 'pre-order', 'preorder', 'скоро']):
                    kind = 'preorder'
                elif any(word in full_content for word in ['в продаже', 'release', 'релиз', 'доступна', 'купить']):
                    kind = 'release'
                elif any(word in full_content for word in ['скидка', 'акция', 'распродажа', 'discount', 'sale']):
                    kind = 'discount'

                # Ищем цены в тексте
                price = None
                price_match = re.search(r'(\d[\d\s]*)\s*₽|(\d+)\s*руб', full_content)
                if price_match:
                    price = float(price_match.group(1) or price_match.group(2))

                # Ищем скидки
                discount_pct = None
                discount_match = re.search(r'скидка\s*(\d+)%|-(\d+)%|(\d+)%\s*скидка', full_content)
                if discount_match:
                    discount_pct = float(discount_match.group(1) or discount_match.group(2) or discount_match.group(3))

                # Извлекаем дату публикации
                publish_date = None
                if date_elem:
                    date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    # Здесь можно добавить парсинг даты, но пока пропускаем

                yield ListingEventDraft(
                    title=title,
                    url=f"https://nastol.io{url}" if url and not url.startswith('http') else url,
                    store_id='nastolio',
                    kind=kind,
                    price=price,
                    discount_pct=discount_pct,
                    in_stock=True  # Для новостей считаем как в наличии
                )

            except Exception as e:
                print(f"Error parsing item: {e}")
                continue


class NastolSpecificArticleAgent(NastolPublicationsAgent):
    """Агент для мониторинга конкретной статьи."""

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Извлечь события из конкретной статьи."""
        soup = BeautifulSoup(fetched.body, 'html.parser')

        # Для конкретной статьи ищем игры в тексте
        content_elem = soup.select_one('.article-content, .post-content')
        if not content_elem:
            return

        content = content_elem.get_text(strip=True).lower()

        # Здесь можно добавить логику поиска названий игр из watchlist
        # и создания событий на их основе

        # Пример - ищем упоминания игр с ключевыми словами
        game_patterns = [
            r'([^,.!?]*?\b(?:предзаказ|пред-заказ)[^,.!?]*?)',
            r'([^,.!?]*?\b(?:в продаже|релиз)[^,.!?]*?)',
            r'([^,.!?]*?\b(?:скидка|акция)[^,.!?]*?)'
        ]

        for pattern in game_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                text = match.group(1).strip()
                if len(text) > 10:  # Фильтруем короткие совпадения
                    kind = 'announce'
                    if 'предзаказ' in text:
                        kind = 'preorder'
                    elif 'в продаже' in text or 'релиз' in text:
                        kind = 'release'
                    elif 'скидка' in text or 'акция' in text:
                        kind = 'discount'

                    yield ListingEventDraft(
                        title=text[:100],  # Обрезаем длинные заголовки
                        url=fetched.url,
                        store_id='nastolio',
                        kind=kind
                    )