"""Initial snapshot of the existing 16-table ORM schema.

Revision ID: 0001
Revises: None
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Frozen schema snapshot; do not import live ORM models here.
    op.create_table('users',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=150), nullable=False),
    sa.Column('role', sa.String(length=30), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('courses',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('domain', sa.String(length=100), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_courses_user_id'), 'courses', ['user_id'], unique=False)
    op.create_table('concepts',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('course_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('difficulty', sa.String(length=20), nullable=True),
    sa.Column('prerequisite_concept_ids', sa.JSON(), nullable=True),
    sa.Column('source_chunk_ids', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_concepts_course_id'), 'concepts', ['course_id'], unique=False)
    op.create_table('documents',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('course_id', sa.String(length=36), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('file_path', sa.Text(), nullable=False),
    sa.Column('file_hash_sha256', sa.String(length=64), nullable=False),
    sa.Column('page_count', sa.Integer(), nullable=False),
    sa.Column('file_size_bytes', sa.Integer(), nullable=False),
    sa.Column('upload_status', sa.String(length=30), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_course_id'), 'documents', ['course_id'], unique=False)
    op.create_table('modules',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('course_id', sa.String(length=36), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('sequence_order', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_modules_course_id'), 'modules', ['course_id'], unique=False)
    op.create_table('project_briefs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('course_id', sa.String(length=36), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('scenario_description', sa.Text(), nullable=False),
    sa.Column('deliverables', sa.JSON(), nullable=False),
    sa.Column('milestone_roadmap', sa.JSON(), nullable=False),
    sa.Column('rubric', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('course_id')
    )
    op.create_table('workflow_tasks',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('course_id', sa.String(length=36), nullable=False),
    sa.Column('task_type', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('retry_count', sa.Integer(), nullable=True),
    sa.Column('error_log', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_tasks_course_id'), 'workflow_tasks', ['course_id'], unique=False)
    op.create_table('concept_mastery',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('concept_id', sa.String(length=36), nullable=False),
    sa.Column('mastery_score', sa.Float(), nullable=True),
    sa.Column('needs_revision', sa.Boolean(), nullable=True),
    sa.Column('last_evaluated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_concept_mastery_concept_id'), 'concept_mastery', ['concept_id'], unique=False)
    op.create_index(op.f('ix_concept_mastery_user_id'), 'concept_mastery', ['user_id'], unique=False)
    op.create_table('content_chunks',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('document_id', sa.String(length=36), nullable=False),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('page_number', sa.Integer(), nullable=False),
    sa.Column('text_content', sa.Text(), nullable=False),
    sa.Column('token_count', sa.Integer(), nullable=False),
    sa.Column('embedding_id', sa.String(length=100), nullable=True),
    sa.Column('metadata_json', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_chunks_document_id'), 'content_chunks', ['document_id'], unique=False)
    op.create_table('lessons',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('module_id', sa.String(length=36), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('sequence_order', sa.Integer(), nullable=False),
    sa.Column('estimated_minutes', sa.Integer(), nullable=True),
    sa.Column('learning_objectives', sa.JSON(), nullable=False),
    sa.Column('target_concept_ids', sa.JSON(), nullable=False),
    sa.Column('source_chunk_ids', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lessons_module_id'), 'lessons', ['module_id'], unique=False)
    op.create_table('learner_events',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('course_id', sa.String(length=36), nullable=False),
    sa.Column('lesson_id', sa.String(length=36), nullable=True),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_learner_events_course_id'), 'learner_events', ['course_id'], unique=False)
    op.create_index(op.f('ix_learner_events_user_id'), 'learner_events', ['user_id'], unique=False)
    op.create_table('lesson_progress',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('lesson_id', sa.String(length=36), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('video_completed', sa.Boolean(), nullable=True),
    sa.Column('quiz_completed', sa.Boolean(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lesson_progress_lesson_id'), 'lesson_progress', ['lesson_id'], unique=False)
    op.create_index(op.f('ix_lesson_progress_user_id'), 'lesson_progress', ['user_id'], unique=False)
    op.create_table('practical_exercises',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('lesson_id', sa.String(length=36), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=False),
    sa.Column('deliverable_description', sa.Text(), nullable=False),
    sa.Column('starter_template', sa.Text(), nullable=True),
    sa.Column('rubric_criteria', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practical_exercises_lesson_id'), 'practical_exercises', ['lesson_id'], unique=False)
    op.create_table('quizzes',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('lesson_id', sa.String(length=36), nullable=False),
    sa.Column('passing_score', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('lesson_id')
    )
    op.create_table('video_assets',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('lesson_id', sa.String(length=36), nullable=False),
    sa.Column('script_json', sa.JSON(), nullable=False),
    sa.Column('slide_deck_json', sa.JSON(), nullable=False),
    sa.Column('audio_path', sa.Text(), nullable=True),
    sa.Column('srt_subtitles_path', sa.Text(), nullable=True),
    sa.Column('video_path', sa.Text(), nullable=True),
    sa.Column('duration_seconds', sa.Integer(), nullable=True),
    sa.Column('generation_status', sa.String(length=30), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('lesson_id')
    )
    op.create_table('quiz_questions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('quiz_id', sa.String(length=36), nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('question_type', sa.String(length=20), nullable=False),
    sa.Column('options', sa.JSON(), nullable=False),
    sa.Column('correct_answer', sa.Text(), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('target_concept_id', sa.String(length=36), nullable=True),
    sa.Column('source_chunk_id', sa.String(length=36), nullable=True),
    sa.Column('sequence_order', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['source_chunk_id'], ['content_chunks.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['target_concept_id'], ['concepts.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quiz_questions_quiz_id'), 'quiz_questions', ['quiz_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # Drop dependents before their referenced tables.
    op.drop_index(op.f('ix_quiz_questions_quiz_id'), table_name='quiz_questions')
    op.drop_table('quiz_questions')
    op.drop_table('video_assets')
    op.drop_table('quizzes')
    op.drop_index(op.f('ix_practical_exercises_lesson_id'), table_name='practical_exercises')
    op.drop_table('practical_exercises')
    op.drop_index(op.f('ix_lesson_progress_user_id'), table_name='lesson_progress')
    op.drop_index(op.f('ix_lesson_progress_lesson_id'), table_name='lesson_progress')
    op.drop_table('lesson_progress')
    op.drop_index(op.f('ix_learner_events_user_id'), table_name='learner_events')
    op.drop_index(op.f('ix_learner_events_course_id'), table_name='learner_events')
    op.drop_table('learner_events')
    op.drop_index(op.f('ix_lessons_module_id'), table_name='lessons')
    op.drop_table('lessons')
    op.drop_index(op.f('ix_content_chunks_document_id'), table_name='content_chunks')
    op.drop_table('content_chunks')
    op.drop_index(op.f('ix_concept_mastery_user_id'), table_name='concept_mastery')
    op.drop_index(op.f('ix_concept_mastery_concept_id'), table_name='concept_mastery')
    op.drop_table('concept_mastery')
    op.drop_index(op.f('ix_workflow_tasks_course_id'), table_name='workflow_tasks')
    op.drop_table('workflow_tasks')
    op.drop_table('project_briefs')
    op.drop_index(op.f('ix_modules_course_id'), table_name='modules')
    op.drop_table('modules')
    op.drop_index(op.f('ix_documents_course_id'), table_name='documents')
    op.drop_table('documents')
    op.drop_index(op.f('ix_concepts_course_id'), table_name='concepts')
    op.drop_table('concepts')
    op.drop_index(op.f('ix_courses_user_id'), table_name='courses')
    op.drop_table('courses')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
