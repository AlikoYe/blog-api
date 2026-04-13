from modeltranslation.translator import TranslationOptions, register

from apps.blog.models import Category


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name",)
