from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from .models import Category, Subcategory, Dish

def menu_list(request):
    """Страница меню – русская кухня по умолчанию, все категории доступны"""
    
    # Получаем параметры фильтрации (оставляем для совместимости, но фильтрацию по категории убираем)
    selected_category_id = request.GET.get('category')
    selected_subcategory_id = request.GET.get('subcategory')
    
    # Получаем все категории, отсортированные по полю order
    categories = list(Category.objects.order_by('order').all())
    
    # Находим категорию "Русская кухня" (по названию, регистронезависимо)
    russian_category = None
    other_categories = []
    for cat in categories:
        if 'русская' in cat.name.lower():
            russian_category = cat
        else:
            other_categories.append(cat)
    
    # Переупорядочиваем: русскую кухню – первой, остальные в исходном порядке
    if russian_category:
        ordered_categories = [russian_category] + other_categories
    else:
        ordered_categories = categories  # если русской нет – оставляем как есть
    
    # Получаем все уникальные подкатегории для верхнего фильтра (без изменений)
    all_subcategories = Subcategory.objects.select_related('category').order_by('name', 'category__order').all()
    subcategories_by_name = {}
    for sub in all_subcategories:
        if sub.name not in subcategories_by_name:
            subcategories_by_name[sub.name] = {
                'id': sub.id,
                'name': sub.name,
                'categories': []
            }
        subcategories_by_name[sub.name]['categories'].append(sub.category.name)
    unique_subcategories = list(subcategories_by_name.values())
    
    # --- Формируем данные для всех категорий (без фильтрации по category) ---
    from collections import defaultdict
    # Берём все доступные блюда (is_available=True)
    all_dishes = Dish.objects.filter(is_available=True).select_related('category', 'subcategory')
    # Группируем по категориям
    dishes_by_category = defaultdict(list)
    for dish in all_dishes.order_by('category__order', 'subcategory__order', 'order'):
        dishes_by_category[dish.category.id].append(dish)
    
    categories_data = []
    for cat in ordered_categories:
        cat_dishes = dishes_by_category.get(cat.id, [])
        if not cat_dishes:
            # Если у категории нет блюд – пропускаем (не показываем таб)
            continue
        
        subcategories = Subcategory.objects.filter(category=cat).order_by('order')
        dishes_without = [d for d in cat_dishes if not d.subcategory]
        
        subcategories_data = []
        for sub in subcategories:
            sub_dishes = [d for d in cat_dishes if d.subcategory and d.subcategory.id == sub.id]
            if sub_dishes:
                subcategories_data.append({
                    'id': sub.id,
                    'name': sub.name,
                    'dishes': sub_dishes
                })
        
        categories_data.append({
            'id': cat.id,
            'name': cat.name,
            'has_subcategories': bool(subcategories_data),
            'subcategories': subcategories_data,
            'dishes_without': dishes_without
        })
    
    # Обработка режима плоского списка (если выбран фильтр по подкатегории)
    selected_subcategory_name = None
    if selected_subcategory_id and selected_subcategory_id.isdigit():
        selected_sub = Subcategory.objects.filter(id=selected_subcategory_id).first()
        if selected_sub:
            selected_subcategory_name = selected_sub.name
            flat_dishes = Dish.objects.filter(is_available=True, subcategory__name=selected_sub.name) \
                                      .order_by('name', 'category__order')
            context = {
                'categories_data': [],
                'flat_dishes': flat_dishes,
                'is_filtered_by_subcategory': True,
                'selected_subcategory_name': selected_subcategory_name,
                'unique_subcategories': unique_subcategories,
                'selected_subcategory_id': selected_subcategory_id,
            }
            return render(request, 'menu/menu_list.html', context)
    
    # Обычный режим (группировка по категориям)
    context = {
        'categories_data': categories_data,
        'unique_subcategories': unique_subcategories,
        'selected_category_id': None,   # не используется
        'selected_subcategory_id': None,
        'is_filtered_by_subcategory': False,
        'flat_dishes': [],
    }
    return render(request, 'menu/menu_list.html', context)

def menu_by_category(request, category_slug):
    """Меню по категории – перенаправляем на основное меню (или можно оставить как есть)"""
    return menu_list(request)

def dish_detail(request, dish_id):
    """Получение детальной информации о блюде (поддерживает AJAX)"""
    dish = get_object_or_404(Dish, id=dish_id, is_available=True)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'id': dish.id,
            'name': dish.name,
            'description': dish.description or 'Описание отсутствует',
            'price': float(dish.price),
            'weight': dish.weight or 'не указан',
            'category': dish.category.name,
            'subcategory': dish.subcategory.name if dish.subcategory else None,
            'image_url': dish.get_image_url() if dish.image else '/static/images/logo.png',
        }
        return JsonResponse(data)
    return render(request, 'menu/dish_detail.html', {'dish': dish})