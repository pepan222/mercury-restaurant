from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Review

def review_list(request):
    """Список отзывов"""
    reviews = Review.objects.filter(is_published=True, is_moderated=True).order_by('-created_at')
    return render(request, 'reviews/review_list.html', {'reviews': reviews})

@login_required
def add_review(request):
    """Добавление отзыва"""
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        Review.objects.create(
            user=request.user,
            rating=rating,
            comment=comment,
            is_moderated=False,
            is_published=False
        )
        
        messages.success(request, 'Спасибо за отзыв! Он будет опубликован после модерации.')
        return redirect('reviews:review_list')
    
    return render(request, 'reviews/add_review.html')
