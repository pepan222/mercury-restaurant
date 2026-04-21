from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from .models import Category, Subcategory, Dish

def menu_list(request):
    """Страница меню с фильтрацией"""
    
    # Получаем параметры фильтрации
    selected_category_id = request.GET.get('category')
    selected_subcategory_id = request.GET.get('subcategory')

    # Если нет ни одного параметра фильтрации - редиректим на категорию "Русская кухня"
    if not selected_category_id and not selected_subcategory_id:
        # Ищем категорию "Русская кухня" по имени (можно заменить на точное совпадение)
        russian_category = Category.objects.filter(name__icontains='Русская').first()
        if russian_category:
            return redirect(f'{request.path}?category={russian_category.id}')
    
    # Получаем все категории
    categories = Category.objects.order_by('order').all()
    
    # Получаем все уникальные подкатегории (без дубликатов по названию)
    all_subcategories = Subcategory.objects.select_related('category').order_by('name', 'category__order').all()
    
    # Группируем подкатегории по названию
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
    
    # Фильтрация блюд
    dishes_query = Dish.objects.filter(is_available=True).select_related('category', 'subcategory')
    
    selected_subcategory_name = None
    
    if selected_category_id and selected_category_id.isdigit():
        dishes_query = dishes_query.filter(category_id=selected_category_id)
    
    if selected_subcategory_id and selected_subcategory_id.isdigit():
        selected_sub = Subcategory.objects.filter(id=selected_subcategory_id).first()
        if selected_sub:
            selected_subcategory_name = selected_sub.name
            # Ищем все блюда, у которых подкатегория имеет такое же название (из любой категории)
            dishes_query = dishes_query.filter(subcategory__name=selected_sub.name)
    
    # Если выбран фильтр по подкатегории, показываем плоский список
    if selected_subcategory_id and selected_subcategory_name:
        flat_dishes = dishes_query.order_by('name', 'category__order')
        
        context = {
            'categories_data': [],  # Пустой список, чтобы не показывать категории
            'flat_dishes': flat_dishes,
            'is_filtered_by_subcategory': True,
            'selected_subcategory_name': selected_subcategory_name,
            'unique_subcategories': unique_subcategories,
            'selected_subcategory_id': selected_subcategory_id,
        }
        return render(request, 'menu/menu_list.html', context)
    
    # Обычный режим (группировка по категориям)
    from collections import defaultdict
    dishes_by_category = defaultdict(list)
    for dish in dishes_query.order_by('category__order', 'subcategory__order', 'order'):
        dishes_by_category[dish.category.id].append(dish)
    
    categories_data = []
    for cat in categories:
        cat_dishes = dishes_by_category.get(cat.id, [])
        
        if not cat_dishes:
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
    
    context = {
        'categories_data': categories_data,
        'unique_subcategories': unique_subcategories,
        'selected_category_id': selected_category_id,
        'selected_subcategory_id': selected_subcategory_id,
        'is_filtered_by_subcategory': False,
        'flat_dishes': [],
    }
    return render(request, 'menu/menu_list.html', context)

def menu_by_category(request, category_slug):
    """Меню по категории"""
    category = get_object_or_404(Category, slug=category_slug)
    return menu_list(request)

def dish_detail(request, dish_id):
    """Получение детальной информации о блюде (поддерживает AJAX)"""
    dish = get_object_or_404(Dish, id=dish_id, is_available=True)
    
    # Если запрос AJAX, возвращаем JSON
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
    
    # Обычный запрос - рендерим страницу (если нужно)
    return render(request, 'menu/dish_detail.html', {'dish': dish})