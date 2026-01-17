import pytest

from tests.utils import DiffTestCase, DiffTestRunner

RUBY_BASIC_CASES = [
    DiffTestCase(
        name="ruby_281_method_definition",
        initial_files={
            "processor.rb": """class Processor
  def process(data)
    data.upcase
  end
end
""",
            "app.rb": """# Initial file
puts 'Hello'
""",
        },
        changed_files={
            "app.rb": """require_relative 'processor'

processor = Processor.new
result = processor.process("hello")
puts result
""",
        },
        must_include=["processor.process", "Processor.new"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add method call",
    ),
    DiffTestCase(
        name="ruby_282_block_yield",
        initial_files={
            "retry_helper.rb": """module RetryHelper
  def with_retry(max_attempts: 3)
    attempts = 0
    begin
      attempts += 1
      yield
    rescue StandardError => e
      retry if attempts < max_attempts
      raise e
    end
  end
end
""",
            "service.rb": """# Initial
class Service
end
""",
        },
        changed_files={
            "service.rb": """require_relative 'retry_helper'

class Service
  include RetryHelper

  def fetch_data
    with_retry(max_attempts: 5) do
      # API call
      raise "Error" if rand < 0.5
    end
  end
end
""",
        },
        must_include=["with_retry", "include RetryHelper"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add block usage",
    ),
    DiffTestCase(
        name="ruby_283_module_mixin",
        initial_files={
            "logging.rb": """module Logging
  def log(message)
    puts "[LOG] \\#{message}"
  end

  def log_error(message)
    puts "[ERROR] \\#{message}"
  end
end
""",
            "worker.rb": """# Initial
class Worker
end
""",
        },
        changed_files={
            "worker.rb": """require_relative 'logging'

class Worker
  include Logging

  def perform
    log("Starting work")
    # Do work
    log("Work completed")
  end
end
""",
        },
        must_include=["include Logging", "log("],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add module mixin",
    ),
    DiffTestCase(
        name="ruby_284_extend",
        initial_files={
            "class_methods.rb": """module ClassMethods
  def find(id)
    # Find by id
    new(id: id)
  end

  def all
    []
  end
end
""",
            "model.rb": """# Initial
class Model
end
""",
        },
        changed_files={
            "model.rb": """require_relative 'class_methods'

class Model
  extend ClassMethods

  attr_reader :id

  def initialize(id:)
    @id = id
  end
end

# Usage
model = Model.find(1)
""",
        },
        must_include=["extend ClassMethods", "Model.find"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add extend",
    ),
    DiffTestCase(
        name="ruby_285_prepend",
        initial_files={
            "wrapper.rb": """module Wrapper
  def process(data)
    puts "Before processing"
    result = super
    puts "After processing"
    result
  end
end
""",
            "handler.rb": """# Initial
class Handler
  def process(data)
    data.upcase
  end
end
""",
        },
        changed_files={
            "handler.rb": """require_relative 'wrapper'

class Handler
  prepend Wrapper

  def process(data)
    data.upcase
  end
end
""",
        },
        must_include=["prepend Wrapper"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add prepend",
    ),
    DiffTestCase(
        name="ruby_286_attr_accessor",
        initial_files={
            "user.rb": """class User
  attr_accessor :name, :email

  def initialize(name:, email:)
    @name = name
    @email = email
  end
end
""",
            "app.rb": """# Initial
puts 'Hello'
""",
        },
        changed_files={
            "app.rb": """require_relative 'user'

user = User.new(name: 'John', email: 'john@example.com')
puts user.name
user.email = 'new@example.com'
""",
        },
        must_include=["user.name", "user.email"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add attr_accessor usage",
    ),
    DiffTestCase(
        name="ruby_287_class_method",
        initial_files={
            "user.rb": """class User
  def self.find(id)
    # Find user by id
    new(id: id, name: "User \\#{id}")
  end

  def self.all
    []
  end

  attr_reader :id, :name

  def initialize(id:, name:)
    @id = id
    @name = name
  end
end
""",
            "controller.rb": """# Initial
class Controller
end
""",
        },
        changed_files={
            "controller.rb": """require_relative 'user'

class Controller
  def show(id)
    @user = User.find(id)
  end

  def index
    @users = User.all
  end
end
""",
        },
        must_include=["User.find", "User.all"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add class method usage",
    ),
    DiffTestCase(
        name="ruby_288_private_method",
        initial_files={
            "service.rb": """class Service
  def process(data)
    validated = validate(data)
    transform(validated)
  end

  private

  def validate(data)
    raise "Invalid" if data.nil?
    data
  end

  def transform(data)
    data.to_s.upcase
  end
end
""",
            "app.rb": """# Initial
puts 'Hello'
""",
        },
        changed_files={
            "app.rb": """require_relative 'service'

service = Service.new
result = service.process("hello")
puts result
""",
        },
        must_include=["service.process"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add private method usage",
    ),
    DiffTestCase(
        name="ruby_289_method_missing",
        initial_files={
            "dynamic_struct.rb": """class DynamicStruct
  def initialize(hash = {})
    @data = hash
  end

  def method_missing(name, *args)
    if name.to_s.end_with?('=')
      @data[name.to_s.chop.to_sym] = args.first
    else
      @data[name]
    end
  end

  def respond_to_missing?(name, include_private = false)
    true
  end
end
""",
            "app.rb": """# Initial
puts 'Hello'
""",
        },
        changed_files={
            "app.rb": """require_relative 'dynamic_struct'

obj = DynamicStruct.new(name: 'John')
puts obj.name
obj.email = 'john@example.com'
puts obj.email
""",
        },
        must_include=["DynamicStruct.new"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add method_missing usage",
    ),
    DiffTestCase(
        name="ruby_290_proc_lambda",
        initial_files={
            "validators.rb": """module Validators
  POSITIVE = ->(x) { x > 0 }
  NON_EMPTY = ->(s) { !s.nil? && !s.empty? }
  EMAIL_FORMAT = ->(e) { e =~ /\\A[^@\\s]+@[^@\\s]+\\z/ }
end
""",
            "form.rb": """# Initial
class Form
end
""",
        },
        changed_files={
            "form.rb": """require_relative 'validators'

class Form
  def validate(data)
    return false unless Validators::POSITIVE.call(data[:age])
    return false unless Validators::NON_EMPTY.call(data[:name])
    return false unless Validators::EMAIL_FORMAT.call(data[:email])
    true
  end
end
""",
        },
        must_include=["Validators::POSITIVE", "Validators::NON_EMPTY"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add proc/lambda usage",
    ),
]


RUBY_ADVANCED_CASES = [
    DiffTestCase(
        name="ruby_291_symbol_to_proc",
        initial_files={
            "user.rb": """class User
  attr_reader :name, :email, :age

  def initialize(name:, email:, age:)
    @name = name
    @email = email
    @age = age
  end
end
""",
            "report.rb": """# Initial
class Report
end
""",
        },
        changed_files={
            "report.rb": """require_relative 'user'

class Report
  def initialize(users)
    @users = users
  end

  def names
    @users.map(&:name)
  end

  def emails
    @users.map(&:email)
  end

  def total_age
    @users.map(&:age).sum
  end
end
""",
        },
        must_include=["map(&:name)", "map(&:email)"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add symbol to proc",
    ),
    DiffTestCase(
        name="ruby_292_struct",
        initial_files={
            "types.rb": """Point = Struct.new(:x, :y) do
  def distance_from_origin
    Math.sqrt(x**2 + y**2)
  end
end

Rectangle = Struct.new(:width, :height) do
  def area
    width * height
  end
end
""",
            "geometry.rb": """# Initial
module Geometry
end
""",
        },
        changed_files={
            "geometry.rb": """require_relative 'types'

module Geometry
  def self.create_point(x, y)
    Point.new(x, y)
  end

  def self.create_rectangle(w, h)
    Rectangle.new(w, h)
  end
end

p = Geometry.create_point(3, 4)
puts p.distance_from_origin
""",
        },
        must_include=["Point.new", "distance_from_origin"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add struct usage",
    ),
    DiffTestCase(
        name="ruby_293_refinement",
        initial_files={
            "string_ext.rb": """module StringExtensions
  refine String do
    def shout
      upcase + "!"
    end

    def whisper
      downcase + "..."
    end
  end
end
""",
            "messenger.rb": """# Initial
class Messenger
end
""",
        },
        changed_files={
            "messenger.rb": """require_relative 'string_ext'

class Messenger
  using StringExtensions

  def loud_message(text)
    text.shout
  end

  def quiet_message(text)
    text.whisper
  end
end
""",
        },
        must_include=["using StringExtensions"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add refinement usage",
    ),
    DiffTestCase(
        name="ruby_294_metaprogramming",
        initial_files={
            "dsl.rb": """module DSL
  def self.define_accessors(*names)
    names.each do |name|
      define_method(name) do
        instance_variable_get("@\\#{name}")
      end

      define_method("\\#{name}=") do |value|
        instance_variable_set("@\\#{name}", value)
      end
    end
  end
end
""",
            "config.rb": """# Initial
class Config
end
""",
        },
        changed_files={
            "config.rb": """require_relative 'dsl'

class Config
  extend DSL

  define_accessors :host, :port, :debug

  def initialize(host: 'localhost', port: 3000, debug: false)
    @host = host
    @port = port
    @debug = debug
  end
end

config = Config.new
puts config.host
config.debug = true
""",
        },
        must_include=["extend DSL", "define_accessors"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add metaprogramming usage",
    ),
    DiffTestCase(
        name="ruby_295_rails_controller",
        initial_files={
            "user.rb": """class User
  attr_accessor :id, :name, :email

  def self.find(id)
    new(id: id, name: "User \\#{id}")
  end

  def initialize(id: nil, name: nil, email: nil)
    @id = id
    @name = name
    @email = email
  end

  def save
    true
  end
end
""",
            "users_controller.rb": """# Initial
class UsersController
end
""",
        },
        changed_files={
            "users_controller.rb": """require_relative 'user'

class UsersController
  def create
    @user = User.new(user_params)
    if @user.save
      redirect_to @user
    else
      render :new
    end
  end

  def show
    @user = User.find(params[:id])
  end

  private

  def user_params
    { name: 'John', email: 'john@example.com' }
  end

  def params
    { id: 1 }
  end

  def redirect_to(user); end
  def render(action); end
end
""",
        },
        must_include=["User.new", "User.find", "@user.save"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Rails controller",
    ),
    DiffTestCase(
        name="ruby_296_rails_model",
        initial_files={
            "order.rb": """class Order
  attr_accessor :id, :user_id, :total

  def initialize(id: nil, user_id: nil, total: 0)
    @id = id
    @user_id = user_id
    @total = total
  end
end
""",
            "user.rb": """# Initial
class User
end
""",
        },
        changed_files={
            "user.rb": """require_relative 'order'

class User
  attr_accessor :id, :name, :orders

  def initialize(id: nil, name: nil)
    @id = id
    @name = name
    @orders = []
  end

  # has_many :orders simulation
  def orders
    @orders ||= []
  end

  def add_order(order)
    order.user_id = @id
    @orders << order
  end
end
""",
        },
        must_include=["add_order", "order.user_id"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Rails model relationship",
    ),
    DiffTestCase(
        name="ruby_297_rails_callback",
        initial_files={
            "callbacks.rb": """module Callbacks
  def self.included(base)
    base.extend(ClassMethods)
  end

  module ClassMethods
    def before_save(*methods)
      @before_save_callbacks ||= []
      @before_save_callbacks.concat(methods)
    end

    def before_save_callbacks
      @before_save_callbacks || []
    end
  end

  def run_callbacks
    self.class.before_save_callbacks.each { |m| send(m) }
  end
end
""",
            "user.rb": """# Initial
class User
end
""",
        },
        changed_files={
            "user.rb": """require_relative 'callbacks'

class User
  include Callbacks

  attr_accessor :email

  before_save :normalize_email

  def save
    run_callbacks
    true
  end

  private

  def normalize_email
    @email = @email.downcase.strip if @email
  end
end
""",
        },
        must_include=["include Callbacks", "before_save", "run_callbacks"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Rails callback",
    ),
    DiffTestCase(
        name="ruby_298_rails_scope",
        initial_files={
            "scopes.rb": """module Scopes
  def self.included(base)
    base.extend(ClassMethods)
  end

  module ClassMethods
    def scope(name, body)
      define_singleton_method(name, &body)
    end
  end
end
""",
            "user.rb": """# Initial
class User
end
""",
        },
        changed_files={
            "user.rb": """require_relative 'scopes'

class User
  include Scopes

  attr_accessor :active, :role

  scope :active, -> { all.select(&:active) }
  scope :admins, -> { all.select { |u| u.role == 'admin' } }

  def self.all
    []
  end
end

# Usage
User.active
User.admins
""",
        },
        must_include=["include Scopes", "scope :active"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Rails scope",
    ),
    DiffTestCase(
        name="ruby_299_rails_concern",
        initial_files={
            "commentable.rb": """module Commentable
  def self.included(base)
    base.class_eval do
      # has_many :comments simulation
      define_method(:comments) { @comments ||= [] }
      define_method(:add_comment) { |c| comments << c }
    end
  end
end
""",
            "post.rb": """# Initial
class Post
end
""",
        },
        changed_files={
            "post.rb": """require_relative 'commentable'

class Post
  include Commentable

  attr_accessor :title, :body

  def initialize(title:, body:)
    @title = title
    @body = body
  end
end

post = Post.new(title: 'Hello', body: 'World')
post.add_comment('Great post!')
""",
        },
        must_include=["include Commentable", "add_comment"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Rails concern",
    ),
    DiffTestCase(
        name="ruby_300_rspec",
        initial_files={
            "user.rb": """class User
  attr_accessor :email

  def initialize(email:)
    @email = email
  end

  def valid?
    email =~ /\\A[^@\\s]+@[^@\\s]+\\z/
  end
end
""",
            "user_spec.rb": """# Initial
describe 'placeholder' do
end
""",
        },
        changed_files={
            "user_spec.rb": """require_relative 'user'

describe User do
  describe '#valid?' do
    it 'returns true for valid email' do
      user = User.new(email: 'test@example.com')
      expect(user.valid?).to be true
    end

    it 'returns false for invalid email' do
      user = User.new(email: 'invalid')
      expect(user.valid?).to be false
    end
  end
end
""",
        },
        must_include=["User.new", "user.valid?"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add RSpec test",
    ),
]


ALL_RUBY_CASES = RUBY_BASIC_CASES + RUBY_ADVANCED_CASES


@pytest.mark.parametrize("case", ALL_RUBY_CASES, ids=lambda c: c.name)
def test_ruby_diff_context(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
