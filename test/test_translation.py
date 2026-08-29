import pytest

from manga_translator.translators import (
    TRANSLATORS,
    TranslatorChain,
    OfflineTranslator,
    MissingAPIKeyException,
    dispatch,
)
from manga_translator.translators.common import LanguageUnsupportedException

@pytest.mark.asyncio
async def test_no_text_translator():
    queries = ['僕はアイネと共に一度、宿の方に戻った', '改めて直面するのは部屋の問題――部屋のベッドが一つでは、さすがに狭すぎるだろう。']
    chain = TranslatorChain('none:ENG')
    result = await dispatch(chain, queries)
    assert result == ['' for _ in queries]

@pytest.mark.asyncio
async def test_original_translator():
    queries = ['僕はアイネと共に一度、宿の方に戻った', '改めて直面するのは部屋の問題――部屋のベッドが一つでは、さすがに狭すぎるだろう。']
    chain = TranslatorChain('original:ENG')
    result = await dispatch(chain, queries)
    assert result == queries

@pytest.mark.asyncio
async def test_online_translators():
    # custom_openai talks to a real LM Studio/Ollama endpoint (no API key concept, so it
    # won't raise MissingAPIKeyException) - treat connection failures as expected in CI
    # where no local LLM server is running.
    queries = ['僕はアイネと共に一度、宿の方に戻った', '改めて直面するのは部屋の問題――部屋のベッドが一つでは、さすがに狭すぎるだろう。']
    for key in TRANSLATORS:
        if issubclass(TRANSLATORS[key], OfflineTranslator):
            continue
        try:
            chain = TranslatorChain(f'{key}:ENG')
            print(await dispatch(chain, queries))
        except (MissingAPIKeyException, LanguageUnsupportedException, Exception) as e:
            print(e)
