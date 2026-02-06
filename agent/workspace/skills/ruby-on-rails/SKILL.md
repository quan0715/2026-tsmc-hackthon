---
name: ruby-on-rails-setup
description: Use this skill to set up Ruby on Rails environment, create Rails applications, generate scaffolds, and understand common Rails patterns. Use when user requests Rails development, Ruby commands, or MVC architecture help.
---

# Ruby on Rails Skill

## Overview

This skill guides you on how to set up and manage a Ruby on Rails development environment, including project creation, common commands, and coding patterns.

## Environment Check

### 1. Check Ruby Version

```
bash(command="ruby --version")
```

### 2. Check Rails Version

```
bash(command="rails --version")
```

### 3. Install Rails (if needed)

```
bash(command="gem install rails")
```

## Creating a New Project

### Basic Application

```
bash(command="rails new my_app")
```

### API-Only Application

```
bash(command="rails new my_api --api")
```

### With PostgreSQL

```
bash(command="rails new my_app --database=postgresql")
```

## Core Commands

### Server Management

Start server:
```
bash(command="rails server")
```

Start console (interactive shell):
```
bash(command="rails console")
```

### Database Management

Create database:
```
bash(command="rails db:create")
```

Run migrations:
```
bash(command="rails db:migrate")
```

Seed database:
```
bash(command="rails db:seed")
```

### Generators

Generate a model:
```
bash(command="rails generate model User name:string email:string")
```

Generate a controller:
```
bash(command="rails generate controller Users index show")
```

Generate a scaffold (Model + View + Controller):
```
bash(command="rails generate scaffold Post title:string body:text")
```

## Few-Shot Examples (Code Patterns)

### 1. ActiveRecord Models

**Goal:** Create a user model with validations and associations.

```ruby
# app/models/user.rb
class User < ApplicationRecord
  has_many :posts, dependent: :destroy
  
  validates :name, presence: true
  validates :email, presence: true, uniqueness: true, format: { with: URI::MailTo::EMAIL_REGEXP }
  
  scope :active, -> { where(active: true) }
  
  def full_name
    "#{first_name} #{last_name}"
  end
end
```

### 2. Controllers (API)

**Goal:** Create a standard RESTful controller for an API.

```ruby
# app/controllers/api/v1/posts_controller.rb
module Api
  module V1
    class PostsController < ApplicationController
      before_action :set_post, only: [:show, :update, :destroy]

      # GET /api/v1/posts
      def index
        @posts = Post.all
        render json: @posts
      end

      # GET /api/v1/posts/1
      def show
        render json: @post
      end

      # POST /api/v1/posts
      def create
        @post = Post.new(post_params)

        if @post.save
          render json: @post, status: :created, location: api_v1_post_url(@post)
        else
          render json: @post.errors, status: :unprocessable_entity
        end
      end

      private
        def set_post
          @post = Post.find(params[:id])
        end

        def post_params
          params.require(:post).permit(:title, :body, :user_id)
        end
    end
  end
end
```

### 3. Routing

**Goal:** dynamic routes for nested resources.

```ruby
# config/routes.rb
Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      resources :users do
        resources :posts, only: [:index, :create]
      end
      
      resources :posts, only: [:show, :update, :destroy]
    end
  end
  
  get '/health', to: 'health#check'
  root "welcome#index"
end
```

### 4. RSpec Testing

**Goal:** Unit test for a model.

```ruby
# spec/models/user_spec.rb
require 'rails_helper'

RSpec.describe User, type: :model do
  describe 'validations' do
    it 'is valid with valid attributes' do
      user = User.new(name: 'Alice', email: 'alice@example.com')
      expect(user).to be_valid
    end

    it 'is not valid without an email' do
      user = User.new(name: 'Bob', email: nil)
      expect(user).to_not be_valid
    end
  end
  
  describe 'associations' do
    it 'has many posts' do
      assc = described_class.reflect_on_association(:posts)
      expect(assc.macro).to eq :has_many
    end
  end
end
```

### 5. Background Jobs (Sidekiq/ActiveJob)

**Goal:** Create a job to send a welcome email.

```ruby
# app/jobs/welcome_email_job.rb
class WelcomeEmailJob < ApplicationJob
  queue_as :default

  def perform(user_id)
    user = User.find(user_id)
    UserMailer.welcome_email(user).deliver_now
  end
end

# Triggering the job:
# WelcomeEmailJob.perform_later(user.id)
```

## Best Practices

1.  **Fat Model, Skinny Controller:** Keep business logic in models or service objects, not in controllers.
2.  **Use partials:** for reusable view components (if using ERB).
3.  **N+1 Queries:** Be careful with database queries. Use `.includes(:association)` to prevent N+1 link problems.
4.  **Strong Parameters:** Always whitelist params in controllers.
5.  **Service Objects:** Extract complex logic into `app/services/`.
6.  **Environment Variables:** Use `dotenv-rails` or `credentials.yml` for secrets. Don't commit secrets.

## Troubleshooting

### "Pending Migration" Error

If you see `ActiveRecord::PendingMigrationError`:

```
bash(command="rails db:migrate")
```

### "Webpacker::Manifest::MissingEntryError" (Older Rails)

Recompile assets:

```
bash(command="rails webpacker:compile")
```

### Server Address Already in Use

Kill the existing server process:

```
bash(command="lsof -i :3000")
# Then kill the PID found
```
