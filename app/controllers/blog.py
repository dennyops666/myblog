@bp.route('/post/<int:post_id>')
def post_detail(post_id):
    """文章详情页面"""
    try:
        # 获取文章详情
        post = db.session.query(Post).options(
            db.joinedload(Post.category),
            db.joinedload(Post.author),
            db.joinedload(Post.tags)
        ).filter(Post.id == post_id).first_or_404()
        
        # 确保 HTML 内容已经渲染
        if post.html_content is None or post.html_content == '':
            post.update_html_content()
            db.session.commit()
        
        # 获取上一篇和下一篇文章
        prev_post = Post.query.filter(
            Post.id < post_id,
            Post.status == PostStatus.PUBLISHED
        ).order_by(Post.id.desc()).first()
        
        next_post = Post.query.filter(
            Post.id > post_id,
            Post.status == PostStatus.PUBLISHED
        ).order_by(Post.id.asc()).first()
        
        # 增加阅读计数
        post.view_count += 1
        db.session.commit()
        
        # 获取评论表单
        form = CommentForm()
        
        # 获取已审核的评论
        comments = Comment.query.filter(
            Comment.post_id == post_id,
            Comment.parent_id == None,
            Comment.status == CommentStatus.APPROVED
        ).order_by(Comment.created_at.desc()).all()
        
        return render_template('blog/post_detail.html',
                             post=post,
                             prev_post=prev_post,
                             next_post=next_post,
                             comments=comments,
                             form=form,
                             current_user=current_user)
    except Exception as e:
        current_app.logger.error(f"获取文章详情失败: {str(e)}")
        abort(404) 