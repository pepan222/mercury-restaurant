from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from .models import Category, Subcategory, Dish

def menu_list(request):
    """Страница меню – показываем все категории, русская кухня по умолчанию активна"""
    
    # Получаем все категории, отсортированные по полю order
    categories = Category.objects.order_by('order').all()
    
    # Переупорядочиваем: категорию "Русская" 
    russian_category = None
    other_categories = []
    for cat in categories:
        if cat.name.lower() == 'Русская': 
            russian_category = cat
        else:
            other_categories.append(cat)
    
    # Если русская категория найдена – ставим её первой, иначе оставляем как есть
    if russian_category:
        ordered_categories = [russian_category] + other_categories
    else:
        ordered_categories = list(categories)
    
    # Для каждой категории собираем блюда
    from collections import defaultdict
    categories_data = []
    
    for cat in ordered_categories:
        # Все блюда категории, доступные для заказа
        cat_dishes = list(Dish.objects.filter(category=cat, is_available=True)
                          .select_related('subcategory')
                          .order_by('subcategory__order', 'order'))
        
        if not cat_dishes:
            
            continue
        
        # Подкатегории этой категории
        subcategories = Subcategory.objects.filter(category=cat).order_by('order')
        
        # Блюда без подкатегории
        dishes_without = [d for d in cat_dishes if not d.subcategory]
        
        # Блюда по подкатегориям
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
    
    # Уникальные подкатегории для фильтра
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
    
    context = {
        'categories_data': categories_data,
        'unique_subcategories': unique_subcategories,
        'selected_category_id': None,     
        'selected_subcategory_id': None,
        'is_filtered_by_subcategory': False,
        'flat_dishes': [],
    }
    return render(request, 'menu/menu_list.html', context)

def menu_by_category(request, category_slug):
    """Меню по категории – перенаправляем на основной список"""
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