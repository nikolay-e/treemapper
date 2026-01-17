import pytest

from tests.utils import DiffTestCase, DiffTestRunner

SCALA_BASIC_CASES = [
    DiffTestCase(
        name="scala_001_case_class",
        initial_files={
            "User.scala": """case class User(name: String, age: Int) {
  def isAdult: Boolean = age >= 18
}

object User {
  def apply(name: String): User = User(name, 0)
}
""",
            "UserService.scala": """class UserService {}
""",
        },
        changed_files={
            "UserService.scala": """class UserService {
  def createUser(name: String, age: Int): User = {
    User(name, age)
  }

  def copyWithNewAge(user: User, newAge: Int): User = {
    user.copy(age = newAge)
  }

  def compareUsers(u1: User, u2: User): Boolean = {
    u1 == u2
  }
}
""",
        },
        must_include=["UserService", "createUser", "copy"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add case class usage",
    ),
    DiffTestCase(
        name="scala_002_trait_mixin",
        initial_files={
            "Logging.scala": """trait Logging {
  def log(message: String): Unit = println(s"[LOG] $message")
  def debug(message: String): Unit = println(s"[DEBUG] $message")
}
""",
            "Metrics.scala": """trait Metrics {
  def recordMetric(name: String, value: Double): Unit = {
    println(s"Metric: $name = $value")
  }
}
""",
            "Service.scala": """class Service {}
""",
        },
        changed_files={
            "Service.scala": """class Service extends Logging with Metrics {
  def process(data: String): Unit = {
    log(s"Processing: $data")
    recordMetric("process_count", 1.0)
    debug("Process complete")
  }
}
""",
        },
        must_include=["Service", "extends Logging with Metrics", "process"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add trait mixin",
    ),
    DiffTestCase(
        name="scala_003_object_singleton",
        initial_files={
            "Config.scala": """object Config {
  val timeout: Int = 30
  val maxRetries: Int = 3
  val baseUrl: String = "https://api.example.com"

  def getFullUrl(path: String): String = s"$baseUrl$path"
}
""",
            "ApiClient.scala": """class ApiClient {}
""",
        },
        changed_files={
            "ApiClient.scala": """class ApiClient {
  def fetch(path: String): String = {
    val url = Config.getFullUrl(path)
    val timeout = Config.timeout
    s"Fetching $url with timeout $timeout"
  }

  def retry(action: => String): String = {
    var attempts = 0
    while (attempts < Config.maxRetries) {
      attempts += 1
    }
    action
  }
}
""",
        },
        must_include=["ApiClient", "Config.getFullUrl", "Config.timeout"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add object singleton usage",
    ),
    DiffTestCase(
        name="scala_004_companion_object",
        initial_files={
            "User.scala": """case class User(id: String, name: String)

object User {
  def apply(name: String): User = User(java.util.UUID.randomUUID().toString, name)

  def fromJson(json: String): User = {
    User("parsed-id", json)
  }

  val anonymous: User = User("anon", "Anonymous")
}
""",
            "UserFactory.scala": """class UserFactory {}
""",
        },
        changed_files={
            "UserFactory.scala": """class UserFactory {
  def createUser(name: String): User = {
    User(name)
  }

  def createFromJson(json: String): User = {
    User.fromJson(json)
  }

  def getAnonymous: User = {
    User.anonymous
  }
}
""",
        },
        must_include=["UserFactory", "User.fromJson", "User.anonymous"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add companion object usage",
    ),
    DiffTestCase(
        name="scala_005_implicit_conversion",
        initial_files={
            "Implicits.scala": """object Implicits {
  implicit def stringToUser(s: String): User = User(s, 0)
  implicit def intToUser(id: Int): User = User(s"user-$id", id)
}

case class User(name: String, age: Int)
""",
            "UserProcessor.scala": """class UserProcessor {}
""",
        },
        changed_files={
            "UserProcessor.scala": """import Implicits._

class UserProcessor {
  def processUser(user: User): String = {
    s"Processing ${user.name}"
  }

  def processString(): String = {
    processUser("John")
  }

  def processId(): String = {
    processUser(42)
  }
}
""",
        },
        must_include=["UserProcessor", "import Implicits._", "processString"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add implicit conversion usage",
    ),
    DiffTestCase(
        name="scala_006_implicit_class",
        initial_files={
            "StringExtensions.scala": """object StringExtensions {
  implicit class RichString(val s: String) extends AnyVal {
    def shout: String = s.toUpperCase + "!"
    def whisper: String = s.toLowerCase + "..."
    def repeat(n: Int): String = s * n
  }
}
""",
            "Formatter.scala": """class Formatter {}
""",
        },
        changed_files={
            "Formatter.scala": """import StringExtensions._

class Formatter {
  def formatLoud(text: String): String = {
    text.shout
  }

  def formatQuiet(text: String): String = {
    text.whisper
  }

  def formatRepeated(text: String, times: Int): String = {
    text.repeat(times)
  }
}
""",
        },
        must_include=["Formatter", "import StringExtensions._", "shout"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add implicit class usage",
    ),
    DiffTestCase(
        name="scala_007_given_using",
        initial_files={
            "Ordering.scala": """case class User(name: String, age: Int)

object UserOrdering {
  given Ordering[User] = Ordering.by(_.name)

  given ageOrdering: Ordering[User] = Ordering.by(_.age)
}
""",
            "UserSorter.scala": """class UserSorter {}
""",
        },
        changed_files={
            "UserSorter.scala": """import UserOrdering.given

class UserSorter {
  def sortByName(users: List[User]): List[User] = {
    users.sorted
  }

  def sortByAge(users: List[User]): List[User] = {
    users.sorted(using UserOrdering.ageOrdering)
  }

  def findMin(users: List[User])(using ord: Ordering[User]): User = {
    users.min
  }
}
""",
        },
        must_include=["UserSorter", "import UserOrdering.given", "sorted"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add given/using",
    ),
    DiffTestCase(
        name="scala_008_type_class",
        initial_files={
            "Show.scala": """trait Show[A] {
  def show(a: A): String
}

object Show {
  def apply[A](implicit sh: Show[A]): Show[A] = sh

  implicit val intShow: Show[Int] = (a: Int) => a.toString
  implicit val stringShow: Show[String] = (a: String) => a
}
""",
            "Printer.scala": """class Printer {}
""",
        },
        changed_files={
            "Printer.scala": """class Printer {
  def print[A: Show](value: A): String = {
    Show[A].show(value)
  }

  def printInt(value: Int): String = {
    print(value)
  }

  def printString(value: String): String = {
    print(value)
  }
}
""",
        },
        must_include=["Printer", "Show[A].show", "print"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add type class usage",
    ),
    DiffTestCase(
        name="scala_009_higher_kinded_type",
        initial_files={
            "Functor.scala": """trait Functor[F[_]] {
  def map[A, B](fa: F[A])(f: A => B): F[B]
}

object Functor {
  implicit val listFunctor: Functor[List] = new Functor[List] {
    def map[A, B](fa: List[A])(f: A => B): List[B] = fa.map(f)
  }

  implicit val optionFunctor: Functor[Option] = new Functor[Option] {
    def map[A, B](fa: Option[A])(f: A => B): Option[B] = fa.map(f)
  }
}
""",
            "FunctorOps.scala": """class FunctorOps {}
""",
        },
        changed_files={
            "FunctorOps.scala": """class FunctorOps {
  def double[F[_]: Functor](container: F[Int]): F[Int] = {
    implicitly[Functor[F]].map(container)(_ * 2)
  }

  def doubleList(list: List[Int]): List[Int] = {
    double(list)
  }

  def doubleOption(opt: Option[Int]): Option[Int] = {
    double(opt)
  }
}
""",
        },
        must_include=["FunctorOps", "Functor[F]", "double"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add higher-kinded type usage",
    ),
    DiffTestCase(
        name="scala_010_path_dependent_type",
        initial_files={
            "Outer.scala": """class Outer {
  class Inner {
    def greet: String = "Hello from Inner"
  }

  type T = Inner

  def createInner: Inner = new Inner
}
""",
            "PathDependent.scala": """class PathDependent {}
""",
        },
        changed_files={
            "PathDependent.scala": """class PathDependent {
  def processInner(outer: Outer)(inner: outer.Inner): String = {
    inner.greet
  }

  def createAndProcess(): String = {
    val outer = new Outer
    val inner: outer.T = outer.createInner
    processInner(outer)(inner)
  }
}
""",
        },
        must_include=["PathDependent", "outer.Inner", "createAndProcess"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add path-dependent type usage",
    ),
]


SCALA_ADVANCED_CASES = [
    DiffTestCase(
        name="scala_011_for_comprehension",
        initial_files={
            "Repository.scala": """case class User(id: String, name: String)
case class Order(id: String, userId: String, total: Double)

class Repository {
  def getUser(id: String): Option[User] = Some(User(id, "John"))
  def getOrders(user: User): Option[List[Order]] = Some(List(Order("o1", user.id, 100.0)))
}
""",
            "OrderService.scala": """class OrderService {}
""",
        },
        changed_files={
            "OrderService.scala": """class OrderService(repo: Repository) {
  def getUserOrders(userId: String): Option[List[Order]] = {
    for {
      user <- repo.getUser(userId)
      orders <- repo.getOrders(user)
    } yield orders
  }

  def getTotalForUser(userId: String): Option[Double] = {
    for {
      user <- repo.getUser(userId)
      orders <- repo.getOrders(user)
      total = orders.map(_.total).sum
    } yield total
  }
}
""",
        },
        must_include=["OrderService", "for {", "yield orders"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add for comprehension",
    ),
    DiffTestCase(
        name="scala_012_pattern_matching",
        initial_files={
            "User.scala": """case class User(name: String, age: Int, email: Option[String])
""",
            "UserValidator.scala": """class UserValidator {}
""",
        },
        changed_files={
            "UserValidator.scala": """class UserValidator {
  def validate(user: User): String = user match {
    case User(name, _, _) if name.isEmpty =>
      "Name cannot be empty"
    case User(_, age, _) if age < 0 =>
      "Age cannot be negative"
    case User(name, age, Some(email)) if email.contains("@") =>
      s"Valid user: $name, $age, $email"
    case User(name, age, None) =>
      s"Valid user without email: $name, $age"
    case _ =>
      "Invalid user"
  }

  def extractEmail(user: User): String = user match {
    case User(_, _, Some(email)) => email
    case User(name, _, None) => s"$name@default.com"
  }
}
""",
        },
        must_include=["UserValidator", "match {", "case User"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add pattern matching",
    ),
    DiffTestCase(
        name="scala_013_partial_function",
        initial_files={
            "Event.scala": """sealed trait Event
case class UserCreated(name: String) extends Event
case class UserDeleted(id: String) extends Event
case class OrderPlaced(orderId: String, amount: Double) extends Event
""",
            "EventHandler.scala": """class EventHandler {}
""",
        },
        changed_files={
            "EventHandler.scala": """class EventHandler {
  val userHandler: PartialFunction[Event, String] = {
    case UserCreated(name) => s"Created user: $name"
    case UserDeleted(id) => s"Deleted user: $id"
  }

  val orderHandler: PartialFunction[Event, String] = {
    case OrderPlaced(id, amount) => s"Order $id: $$$amount"
  }

  val combinedHandler: PartialFunction[Event, String] =
    userHandler orElse orderHandler

  def handle(event: Event): Option[String] = {
    combinedHandler.lift(event)
  }
}
""",
        },
        must_include=["EventHandler", "PartialFunction", "orElse"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add partial function",
    ),
    DiffTestCase(
        name="scala_014_future",
        initial_files={
            "ExpensiveComputation.scala": """object ExpensiveComputation {
  def compute(input: Int): Int = {
    Thread.sleep(100)
    input * 2
  }

  def computeString(input: String): String = {
    Thread.sleep(100)
    input.toUpperCase
  }
}
""",
            "AsyncProcessor.scala": """class AsyncProcessor {}
""",
        },
        changed_files={
            "AsyncProcessor.scala": """import scala.concurrent.{Future, ExecutionContext}
import scala.concurrent.ExecutionContext.Implicits.global

class AsyncProcessor {
  def processAsync(input: Int): Future[Int] = Future {
    ExpensiveComputation.compute(input)
  }

  def processMany(inputs: List[Int]): Future[List[Int]] = {
    Future.sequence(inputs.map(i => Future(ExpensiveComputation.compute(i))))
  }

  def processCombined(a: Int, b: String): Future[(Int, String)] = {
    for {
      resultA <- Future(ExpensiveComputation.compute(a))
      resultB <- Future(ExpensiveComputation.computeString(b))
    } yield (resultA, resultB)
  }
}
""",
        },
        must_include=["AsyncProcessor", "Future", "Future.sequence"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Future usage",
    ),
]


SCALA_AKKA_CASES = [
    DiffTestCase(
        name="scala_021_akka_actor",
        initial_files={
            "Messages.scala": """sealed trait UserMessage
case class CreateUser(name: String) extends UserMessage
case class DeleteUser(id: String) extends UserMessage
case class GetUser(id: String) extends UserMessage
case class UserCreated(id: String, name: String)
""",
            "UserActor.scala": """class UserActor {}
""",
        },
        changed_files={
            "UserActor.scala": """import akka.actor.{Actor, ActorLogging, Props}

class UserActor extends Actor with ActorLogging {
  private var users: Map[String, String] = Map.empty

  def receive: Receive = {
    case CreateUser(name) =>
      val id = java.util.UUID.randomUUID().toString
      users = users + (id -> name)
      log.info(s"Created user $id: $name")
      sender() ! UserCreated(id, name)

    case DeleteUser(id) =>
      users = users - id
      log.info(s"Deleted user $id")

    case GetUser(id) =>
      sender() ! users.get(id)
  }
}

object UserActor {
  def props: Props = Props[UserActor]()
}
""",
        },
        must_include=["UserActor", "Actor", "def receive"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Akka actor",
    ),
    DiffTestCase(
        name="scala_022_play_controller",
        initial_files={
            "routes": """GET     /users/:id        controllers.UserController.getUser(id: Long)
POST    /users            controllers.UserController.createUser()
DELETE  /users/:id        controllers.UserController.deleteUser(id: Long)
""",
            "UserController.scala": """class UserController {}
""",
        },
        changed_files={
            "UserController.scala": """import play.api.mvc._
import play.api.libs.json._
import scala.concurrent.{ExecutionContext, Future}

case class User(id: Long, name: String)

class UserController(cc: ControllerComponents)(implicit ec: ExecutionContext)
    extends AbstractController(cc) {

  implicit val userFormat: Format[User] = Json.format[User]

  def getUser(id: Long): Action[AnyContent] = Action.async {
    Future.successful(Ok(Json.toJson(User(id, "John"))))
  }

  def createUser(): Action[JsValue] = Action.async(parse.json) { request =>
    request.body.validate[User].fold(
      errors => Future.successful(BadRequest(Json.obj("error" -> "Invalid JSON"))),
      user => Future.successful(Created(Json.toJson(user)))
    )
  }

  def deleteUser(id: Long): Action[AnyContent] = Action.async {
    Future.successful(NoContent)
  }
}
""",
        },
        must_include=["UserController", "AbstractController", "Action.async"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Play controller",
    ),
    DiffTestCase(
        name="scala_023_slick_query",
        initial_files={
            "Tables.scala": """import slick.jdbc.PostgresProfile.api._

case class User(id: Long, name: String, age: Int, active: Boolean)

class Users(tag: Tag) extends Table[User](tag, "users") {
  def id = column[Long]("id", O.PrimaryKey, O.AutoInc)
  def name = column[String]("name")
  def age = column[Int]("age")
  def active = column[Boolean]("active")
  def * = (id, name, age, active).mapTo[User]
}

object Tables {
  val users = TableQuery[Users]
}
""",
            "UserRepository.scala": """class UserRepository {}
""",
        },
        changed_files={
            "UserRepository.scala": """import slick.jdbc.PostgresProfile.api._
import scala.concurrent.Future

class UserRepository(db: Database) {
  import Tables._

  def findAdults(): Future[Seq[User]] = {
    db.run(users.filter(_.age >= 18).result)
  }

  def findActive(): Future[Seq[User]] = {
    db.run(users.filter(_.active === true).result)
  }

  def findByName(name: String): Future[Option[User]] = {
    db.run(users.filter(_.name === name).result.headOption)
  }

  def countByAge(minAge: Int): Future[Int] = {
    db.run(users.filter(_.age >= minAge).length.result)
  }
}
""",
        },
        must_include=["UserRepository", "Tables._", "db.run"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Slick query",
    ),
]


SCALA_CATS_CASES = [
    DiffTestCase(
        name="scala_031_cats_effect",
        initial_files={
            "Database.scala": """import cats.effect.IO

object Database {
  def connect(): IO[Unit] = IO(println("Connected"))
  def disconnect(): IO[Unit] = IO(println("Disconnected"))
  def query(sql: String): IO[List[String]] = IO(List("result1", "result2"))
}
""",
            "Program.scala": """object Program {}
""",
        },
        changed_files={
            "Program.scala": """import cats.effect.{IO, IOApp, ExitCode}
import cats.syntax.all._

object Program extends IOApp {
  def program: IO[Unit] = for {
    _ <- Database.connect()
    results <- Database.query("SELECT * FROM users")
    _ <- IO(results.foreach(println))
    _ <- Database.disconnect()
  } yield ()

  def run(args: List[String]): IO[ExitCode] = {
    program.as(ExitCode.Success)
  }
}
""",
        },
        must_include=["Program", "IOApp", "Database.connect"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Cats Effect IO",
    ),
    DiffTestCase(
        name="scala_032_zio",
        initial_files={
            "Client.scala": """import zio._

trait Client {
  def fetch(url: String): Task[String]
}

object Client {
  val live: ULayer[Client] = ZLayer.succeed(new Client {
    def fetch(url: String): Task[String] = ZIO.succeed(s"Response from $url")
  })
}
""",
            "DataFetcher.scala": """object DataFetcher {}
""",
        },
        changed_files={
            "DataFetcher.scala": """import zio._

case class Data(content: String)

object DataFetcher {
  def fetch(url: String): ZIO[Client, Throwable, Data] = {
    for {
      client <- ZIO.service[Client]
      response <- client.fetch(url)
    } yield Data(response)
  }

  def fetchMultiple(urls: List[String]): ZIO[Client, Throwable, List[Data]] = {
    ZIO.foreach(urls)(fetch)
  }
}
""",
        },
        must_include=["DataFetcher", "ZIO.service", "ZIO.foreach"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add ZIO",
    ),
    DiffTestCase(
        name="scala_033_scalatest",
        initial_files={
            "User.scala": """case class User(name: String, email: String) {
  def isValidEmail: Boolean = email.contains("@") && email.contains(".")
  def normalizedEmail: String = email.toLowerCase.trim
}
""",
            "UserSpec.scala": """class UserSpec {}
""",
        },
        changed_files={
            "UserSpec.scala": """import org.scalatest.flatspec.AnyFlatSpec
import org.scalatest.matchers.should.Matchers

class UserSpec extends AnyFlatSpec with Matchers {
  "User" should "have valid email" in {
    val user = User("John", "john@example.com")
    user.isValidEmail should be(true)
  }

  it should "reject invalid email" in {
    val user = User("John", "invalid-email")
    user.isValidEmail should be(false)
  }

  it should "normalize email" in {
    val user = User("John", "  JOHN@Example.COM  ")
    user.normalizedEmail should equal("john@example.com")
  }

  "User creation" should "preserve name" in {
    val user = User("Jane Doe", "jane@test.com")
    user.name should be("Jane Doe")
  }
}
""",
        },
        must_include=["UserSpec", "AnyFlatSpec", "should be"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add ScalaTest",
    ),
]


SCALA_COLLECTIONS_CASES = [
    DiffTestCase(
        name="scala_041_collections_ops",
        initial_files={
            "Data.scala": """case class Data(id: Int, value: String, score: Double)
""",
            "DataProcessor.scala": """class DataProcessor {}
""",
        },
        changed_files={
            "DataProcessor.scala": """class DataProcessor {
  def filterByScore(items: List[Data], minScore: Double): List[Data] = {
    items.filter(_.score >= minScore)
  }

  def groupByFirstChar(items: List[Data]): Map[Char, List[Data]] = {
    items.groupBy(_.value.headOption.getOrElse('_'))
  }

  def topN(items: List[Data], n: Int): List[Data] = {
    items.sortBy(-_.score).take(n)
  }

  def averageScore(items: List[Data]): Double = {
    if (items.isEmpty) 0.0
    else items.map(_.score).sum / items.size
  }

  def flatMapValues(items: List[Data]): List[Char] = {
    items.flatMap(_.value.toList)
  }
}
""",
        },
        must_include=["DataProcessor", "filter", "groupBy", "sortBy"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add collections operations",
    ),
    DiffTestCase(
        name="scala_042_sealed_trait_adt",
        initial_files={
            "Expression.scala": """sealed trait Expression
case class Number(value: Double) extends Expression
case class Add(left: Expression, right: Expression) extends Expression
case class Multiply(left: Expression, right: Expression) extends Expression
case class Variable(name: String) extends Expression
""",
            "Evaluator.scala": """class Evaluator {}
""",
        },
        changed_files={
            "Evaluator.scala": """class Evaluator {
  def evaluate(expr: Expression, vars: Map[String, Double] = Map.empty): Double = expr match {
    case Number(value) => value
    case Add(left, right) => evaluate(left, vars) + evaluate(right, vars)
    case Multiply(left, right) => evaluate(left, vars) * evaluate(right, vars)
    case Variable(name) => vars.getOrElse(name, 0.0)
  }

  def simplify(expr: Expression): Expression = expr match {
    case Add(Number(0), right) => simplify(right)
    case Add(left, Number(0)) => simplify(left)
    case Multiply(Number(1), right) => simplify(right)
    case Multiply(left, Number(1)) => simplify(left)
    case Multiply(Number(0), _) => Number(0)
    case Multiply(_, Number(0)) => Number(0)
    case Add(left, right) => Add(simplify(left), simplify(right))
    case Multiply(left, right) => Multiply(simplify(left), simplify(right))
    case other => other
  }
}
""",
        },
        must_include=["Evaluator", "evaluate", "simplify"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add sealed trait ADT evaluation",
    ),
    DiffTestCase(
        name="scala_043_extension_methods",
        initial_files={
            "IntExtensions.scala": """object IntExtensions {
  extension (n: Int) {
    def squared: Int = n * n
    def isEven: Boolean = n % 2 == 0
    def times(f: => Unit): Unit = (1 to n).foreach(_ => f)
  }
}
""",
            "Calculator.scala": """class Calculator {}
""",
        },
        changed_files={
            "Calculator.scala": """import IntExtensions._

class Calculator {
  def squareSum(nums: List[Int]): Int = {
    nums.map(_.squared).sum
  }

  def countEven(nums: List[Int]): Int = {
    nums.count(_.isEven)
  }

  def repeatAction(n: Int, action: => Unit): Unit = {
    n.times(action)
  }
}
""",
        },
        must_include=["Calculator", "import IntExtensions._", "squared"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add extension methods usage",
    ),
    DiffTestCase(
        name="scala_044_opaque_types",
        initial_files={
            "Types.scala": """object Types {
  opaque type UserId = Long
  opaque type OrderId = Long

  object UserId {
    def apply(value: Long): UserId = value
    extension (id: UserId) def value: Long = id
  }

  object OrderId {
    def apply(value: Long): OrderId = value
    extension (id: OrderId) def value: Long = id
  }
}
""",
            "UserService.scala": """class UserService {}
""",
        },
        changed_files={
            "UserService.scala": """import Types._

class UserService {
  def getUserById(id: UserId): Option[String] = {
    Some(s"User with id ${id.value}")
  }

  def createUser(name: String): UserId = {
    UserId(System.currentTimeMillis())
  }

  def getOrderForUser(userId: UserId, orderId: OrderId): String = {
    s"Order ${orderId.value} for user ${userId.value}"
  }
}
""",
        },
        must_include=["UserService", "import Types._", "UserId"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add opaque types usage",
    ),
]


SCALA_BUILD_CASES = [
    DiffTestCase(
        name="scala_051_build_sbt",
        initial_files={
            "build.sbt": """name := "myapp"
version := "0.1.0"
scalaVersion := "3.3.0"

libraryDependencies ++= Seq(
  "org.typelevel" %% "cats-core" % "2.9.0"
)
""",
            "src/main/scala/Main.scala": """import cats.syntax.all._

object Main extends App {
  println("Hello")
}
""",
        },
        changed_files={
            "build.sbt": """name := "myapp"
version := "0.1.0"
scalaVersion := "3.3.0"

libraryDependencies ++= Seq(
  "org.typelevel" %% "cats-core" % "2.9.0",
  "org.typelevel" %% "cats-effect" % "3.5.0",
  "co.fs2" %% "fs2-core" % "3.7.0",
  "org.scalatest" %% "scalatest" % "3.2.15" % Test
)

scalacOptions ++= Seq(
  "-deprecation",
  "-feature",
  "-Xfatal-warnings"
)
""",
        },
        must_include=["build.sbt", "cats-effect", "fs2-core"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Cats Effect and FS2 dependencies",
    ),
    DiffTestCase(
        name="scala_052_application_conf",
        initial_files={
            "src/main/resources/application.conf": """app {
  name = "myapp"
  port = 8080
}
""",
            "src/main/scala/Config.scala": """import com.typesafe.config.ConfigFactory

object Config {
  private val config = ConfigFactory.load()
  val appName: String = config.getString("app.name")
  val port: Int = config.getInt("app.port")
}
""",
        },
        changed_files={
            "src/main/resources/application.conf": """app {
  name = "myapp"
  port = 8080
  database {
    url = "jdbc:postgresql://localhost/db"
    pool-size = 10
    timeout = 30s
  }
  kafka {
    bootstrap-servers = "localhost:9092"
    topic = "events"
  }
}
""",
        },
        must_include=["application.conf", "database", "kafka"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add database and Kafka configuration",
    ),
]


ALL_SCALA_CASES = (
    SCALA_BASIC_CASES + SCALA_ADVANCED_CASES + SCALA_AKKA_CASES + SCALA_CATS_CASES + SCALA_COLLECTIONS_CASES + SCALA_BUILD_CASES
)


@pytest.mark.parametrize("case", ALL_SCALA_CASES, ids=lambda c: c.name)
def test_scala_diff_context(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
