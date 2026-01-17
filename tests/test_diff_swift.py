import pytest

from tests.utils import DiffTestCase, DiffTestRunner

SWIFT_PROTOCOL_CASES = [
    DiffTestCase(
        name="swift_321_protocol_conformance",
        initial_files={
            "User.swift": """struct User: Codable, Equatable {
    let id: String
    let name: String
    let email: String
}
// garbage_marker_12345 - this should not appear in context
""",
            "UserService.swift": """// Initial
class UserService {}
""",
        },
        changed_files={
            "UserService.swift": """import Foundation

class UserService {
    func encode(user: User) throws -> Data {
        let encoder = JSONEncoder()
        return try encoder.encode(user)
    }

    func decode(data: Data) throws -> User {
        let decoder = JSONDecoder()
        return try decoder.decode(User.self, from: data)
    }
}
""",
        },
        must_include=["UserService", "User", "encode"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add protocol conformance usage",
    ),
    DiffTestCase(
        name="swift_322_extension",
        initial_files={
            "StringExtensions.swift": """extension String {
    func isValidEmail() -> Bool {
        let pattern = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Za-z]{2,}"
        return self.range(of: pattern, options: .regularExpression) != nil
    }

    var trimmed: String {
        trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
// unused_marker_67890
""",
            "Validator.swift": """// Initial
struct Validator {}
""",
        },
        changed_files={
            "Validator.swift": """struct Validator {
    func validateEmail(_ email: String) -> Bool {
        return email.trimmed.isValidEmail()
    }
}
""",
        },
        must_include=["Validator", "validateEmail", "trimmed", "isValidEmail"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add extension usage",
    ),
    DiffTestCase(
        name="swift_323_protocol_extension",
        initial_files={
            "NumericExtensions.swift": """extension Collection where Element: Numeric {
    var sum: Element {
        reduce(0, +)
    }

    var average: Double where Element: BinaryInteger {
        guard !isEmpty else { return 0 }
        return Double(sum) / Double(count)
    }
}
// garbage_marker_12345
""",
            "Calculator.swift": """// Initial
struct Calculator {}
""",
        },
        changed_files={
            "Calculator.swift": """struct Calculator {
    func totalScore(scores: [Int]) -> Int {
        return scores.sum
    }

    func averageScore(scores: [Int]) -> Double {
        return scores.average
    }
}
""",
        },
        must_include=["Calculator", "totalScore", "sum", "average"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add protocol extension usage",
    ),
]


SWIFT_OPTIONAL_CASES = [
    DiffTestCase(
        name="swift_324_optional_binding",
        initial_files={
            "UserRepository.swift": """struct User {
    let id: String
    let name: String
}

class UserRepository {
    private var users: [String: User] = [:]

    func fetchUser(id: String) -> User? {
        return users[id]
    }

    func save(user: User) {
        users[user.id] = user
    }
}
// unused_marker_67890
""",
            "UserController.swift": """// Initial
class UserController {}
""",
        },
        changed_files={
            "UserController.swift": """class UserController {
    let repository = UserRepository()

    func showUser(id: String) -> String {
        if let user = repository.fetchUser(id: id) {
            return "User: \\(user.name)"
        } else {
            return "User not found"
        }
    }
}
""",
        },
        must_include=["UserController", "showUser", "UserRepository", "fetchUser"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add optional binding",
    ),
    DiffTestCase(
        name="swift_325_guard_statement",
        initial_files={
            "Response.swift": """struct Response {
    let data: Data?
    let error: Error?
    let statusCode: Int
}
// garbage_marker_12345
""",
            "NetworkHandler.swift": """// Initial
struct NetworkHandler {}
""",
        },
        changed_files={
            "NetworkHandler.swift": """import Foundation

struct NetworkHandler {
    func handleResponse(_ response: Response) -> Data? {
        guard response.error == nil else {
            print("Error: \\(response.error!)")
            return nil
        }

        guard response.statusCode == 200 else {
            print("Invalid status: \\(response.statusCode)")
            return nil
        }

        guard let data = response.data else {
            print("No data")
            return nil
        }

        return data
    }
}
""",
        },
        must_include=["NetworkHandler", "handleResponse", "Response"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add guard statement",
    ),
    DiffTestCase(
        name="swift_326_result_type",
        initial_files={
            "APIError.swift": """enum APIError: Error {
    case networkError
    case invalidResponse
    case decodingError
}
// unused_marker_67890
""",
            "DataLoader.swift": """// Initial
struct DataLoader {}
""",
        },
        changed_files={
            "DataLoader.swift": """import Foundation

struct DataLoader {
    func load(from url: URL) -> Result<Data, APIError> {
        guard let data = "test".data(using: .utf8) else {
            return .failure(.invalidResponse)
        }
        return .success(data)
    }

    func process(url: URL) {
        let result = load(from: url)
        switch result {
        case .success(let data):
            print("Loaded \\(data.count) bytes")
        case .failure(let error):
            print("Error: \\(error)")
        }
    }
}
""",
        },
        must_include=["DataLoader", "load", "APIError"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add result type",
    ),
]


SWIFT_CONCURRENCY_CASES = [
    DiffTestCase(
        name="swift_327_async_await",
        initial_files={
            "User.swift": """struct User: Codable {
    let id: String
    let name: String
}
// garbage_marker_12345
""",
            "UserAPI.swift": """// Initial
class UserAPI {}
""",
        },
        changed_files={
            "UserAPI.swift": """import Foundation

class UserAPI {
    func fetchUsers() async throws -> [User] {
        let url = URL(string: "https://api.example.com/users")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode([User].self, from: data)
    }

    func getUser(id: String) async throws -> User {
        let users = try await fetchUsers()
        guard let user = users.first(where: { $0.id == id }) else {
            throw NSError(domain: "UserAPI", code: 404)
        }
        return user
    }
}
""",
        },
        must_include=["UserAPI", "fetchUsers", "User"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add async/await",
    ),
    DiffTestCase(
        name="swift_328_actor",
        initial_files={
            "Item.swift": """struct Item: Identifiable {
    let id: String
    let name: String
}
// unused_marker_67890
""",
            "DataStore.swift": """// Initial
class DataStore {}
""",
        },
        changed_files={
            "DataStore.swift": """actor DataStore {
    private var items: [Item] = []

    func add(_ item: Item) {
        items.append(item)
    }

    func remove(id: String) {
        items.removeAll { $0.id == id }
    }

    func getAll() -> [Item] {
        return items
    }

    var count: Int {
        items.count
    }
}
""",
        },
        must_include=["DataStore", "Item", "add"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add actor",
    ),
]


SWIFT_COMBINE_CASES = [
    DiffTestCase(
        name="swift_329_property_wrapper",
        initial_files={
            "Published.swift": """import Combine

@propertyWrapper
struct Published<Value> {
    private var value: Value
    private let subject = PassthroughSubject<Value, Never>()

    var wrappedValue: Value {
        get { value }
        set {
            value = newValue
            subject.send(newValue)
        }
    }

    var projectedValue: PassthroughSubject<Value, Never> {
        subject
    }

    init(wrappedValue: Value) {
        self.value = wrappedValue
    }
}
// garbage_marker_12345
""",
            "ViewModel.swift": """// Initial
class ViewModel {}
""",
        },
        changed_files={
            "ViewModel.swift": """import Combine

class ViewModel: ObservableObject {
    @Published var users: [String] = []
    @Published var isLoading = false

    private var cancellables = Set<AnyCancellable>()

    func loadUsers() {
        isLoading = true
        users = ["John", "Jane"]
        isLoading = false
    }
}
""",
        },
        must_include=["ViewModel", "loadUsers", "Published"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add property wrapper",
    ),
    DiffTestCase(
        name="swift_330_combine_publisher",
        initial_files={
            "SearchService.swift": """import Combine

class SearchService {
    func search(query: String) -> AnyPublisher<[String], Never> {
        Just(["Result 1", "Result 2"])
            .eraseToAnyPublisher()
    }
}
// unused_marker_67890
""",
            "SearchViewModel.swift": """// Initial
class SearchViewModel {}
""",
        },
        changed_files={
            "SearchViewModel.swift": """import Combine

class SearchViewModel: ObservableObject {
    @Published var searchText = ""
    @Published var results: [String] = []

    private let service = SearchService()
    private var cancellables = Set<AnyCancellable>()

    init() {
        $searchText
            .debounce(for: .milliseconds(300), scheduler: RunLoop.main)
            .removeDuplicates()
            .flatMap { [weak self] query in
                self?.service.search(query: query) ?? Just([]).eraseToAnyPublisher()
            }
            .assign(to: &$results)
    }
}
""",
        },
        must_include=["SearchViewModel", "SearchService", "search"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Combine publisher",
    ),
]


SWIFT_SWIFTUI_CASES = [
    DiffTestCase(
        name="swift_331_swiftui_view",
        initial_files={
            "User.swift": """struct User: Identifiable {
    let id: String
    let name: String
    let email: String
}
// garbage_marker_12345
""",
            "UserView.swift": """// Initial
import SwiftUI
struct UserView: View {
    var body: some View { Text("") }
}
""",
        },
        changed_files={
            "UserView.swift": """import SwiftUI

struct UserView: View {
    let user: User

    var body: some View {
        VStack(alignment: .leading) {
            Text(user.name)
                .font(.headline)
            Text(user.email)
                .font(.subheadline)
                .foregroundColor(.gray)
        }
    }
}
""",
        },
        must_include=["UserView", "User"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add SwiftUI view",
    ),
    DiffTestCase(
        name="swift_332_state",
        initial_files={
            "ContentView.swift": """// Initial
import SwiftUI
struct ContentView: View {
    var body: some View { Text("") }
}
// unused_marker_67890
""",
        },
        changed_files={
            "ContentView.swift": """import SwiftUI

struct ContentView: View {
    @State private var isLoading = false
    @State private var items: [String] = []

    var body: some View {
        VStack {
            if isLoading {
                ProgressView()
            } else {
                List(items, id: \\.self) { item in
                    Text(item)
                }
            }
            Button("Load") {
                isLoading = true
            }
        }
    }
}
""",
        },
        must_include=["ContentView", "State", "isLoading"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add @State",
    ),
    DiffTestCase(
        name="swift_333_binding",
        initial_files={
            "User.swift": """struct User {
    var name: String
    var email: String
}
// garbage_marker_12345
""",
            "UserEditor.swift": """// Initial
import SwiftUI
struct UserEditor: View {
    var body: some View { Text("") }
}
""",
        },
        changed_files={
            "UserEditor.swift": """import SwiftUI

struct UserEditor: View {
    @Binding var selectedUser: User?

    var body: some View {
        if let user = selectedUser {
            Form {
                TextField("Name", text: Binding(
                    get: { user.name },
                    set: { selectedUser?.name = $0 }
                ))
                TextField("Email", text: Binding(
                    get: { user.email },
                    set: { selectedUser?.email = $0 }
                ))
            }
        } else {
            Text("No user selected")
        }
    }
}
""",
        },
        must_include=["UserEditor", "Binding", "User"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add @Binding",
    ),
    DiffTestCase(
        name="swift_334_observed_object",
        initial_files={
            "UserViewModel.swift": """import Combine

class UserViewModel: ObservableObject {
    @Published var name = ""
    @Published var email = ""
    @Published var isValid = false

    func validate() {
        isValid = !name.isEmpty && email.contains("@")
    }
}
// unused_marker_67890
""",
            "UserFormView.swift": """// Initial
import SwiftUI
struct UserFormView: View {
    var body: some View { Text("") }
}
""",
        },
        changed_files={
            "UserFormView.swift": """import SwiftUI

struct UserFormView: View {
    @ObservedObject var viewModel: UserViewModel

    var body: some View {
        Form {
            TextField("Name", text: $viewModel.name)
            TextField("Email", text: $viewModel.email)
            Button("Submit") {
                viewModel.validate()
            }
            .disabled(!viewModel.isValid)
        }
        .onChange(of: viewModel.name) { _ in viewModel.validate() }
        .onChange(of: viewModel.email) { _ in viewModel.validate() }
    }
}
""",
        },
        must_include=["UserFormView", "UserViewModel", "ObservedObject"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add @ObservedObject",
    ),
    DiffTestCase(
        name="swift_335_environment_object",
        initial_files={
            "AppState.swift": """import Combine

class AppState: ObservableObject {
    @Published var currentUser: String?
    @Published var isLoggedIn = false

    func login(username: String) {
        currentUser = username
        isLoggedIn = true
    }

    func logout() {
        currentUser = nil
        isLoggedIn = false
    }
}
// garbage_marker_12345
""",
            "ProfileView.swift": """// Initial
import SwiftUI
struct ProfileView: View {
    var body: some View { Text("") }
}
""",
        },
        changed_files={
            "ProfileView.swift": """import SwiftUI

struct ProfileView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        VStack {
            if appState.isLoggedIn {
                Text("Welcome, \\(appState.currentUser ?? "")")
                Button("Logout") {
                    appState.logout()
                }
            } else {
                Text("Please log in")
            }
        }
    }
}
""",
        },
        must_include=["ProfileView", "AppState", "EnvironmentObject"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add @EnvironmentObject",
    ),
]


SWIFT_DATA_CASES = [
    DiffTestCase(
        name="swift_336_coredata_entity",
        initial_files={
            "User+CoreDataProperties.swift": """import Foundation
import CoreData

extension User {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<User> {
        return NSFetchRequest<User>(entityName: "User")
    }

    @NSManaged public var id: UUID?
    @NSManaged public var name: String?
    @NSManaged public var email: String?
    @NSManaged public var createdAt: Date?
}
// unused_marker_67890
""",
            "UserManager.swift": """// Initial
class UserManager {}
""",
        },
        changed_files={
            "UserManager.swift": """import CoreData

class UserManager {
    let context: NSManagedObjectContext

    init(context: NSManagedObjectContext) {
        self.context = context
    }

    func createUser(name: String, email: String) -> User {
        let user = User(context: context)
        user.id = UUID()
        user.name = name
        user.email = email
        user.createdAt = Date()
        return user
    }

    func fetchUsers() throws -> [User] {
        let request = User.fetchRequest()
        return try context.fetch(request)
    }
}
""",
        },
        must_include=["UserManager", "User", "createUser", "fetchRequest"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add CoreData entity usage",
    ),
    DiffTestCase(
        name="swift_337_codable",
        initial_files={
            "User.swift": """struct User: Codable {
    let id: String
    let name: String
    let email: String
}
// garbage_marker_12345
""",
            "APIResponse.swift": """struct APIResponse<T: Codable>: Decodable {
    let data: T
    let status: String
    let timestamp: Date
}
""",
            "APIClient.swift": """// Initial
class APIClient {}
""",
        },
        changed_files={
            "APIClient.swift": """import Foundation

class APIClient {
    func fetchUsers(completion: @escaping (Result<APIResponse<[User]>, Error>) -> Void) {
        let url = URL(string: "https://api.example.com/users")!
        URLSession.shared.dataTask(with: url) { data, _, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            guard let data = data else { return }
            do {
                let decoder = JSONDecoder()
                decoder.dateDecodingStrategy = .iso8601
                let response = try decoder.decode(APIResponse<[User]>.self, from: data)
                completion(.success(response))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
}
""",
        },
        must_include=["APIClient", "fetchUsers", "User", "APIResponse"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Codable decoding",
    ),
]


SWIFT_ERROR_CASES = [
    DiffTestCase(
        name="swift_338_error_handling",
        initial_files={
            "AppError.swift": """enum AppError: Error {
    case networkError(String)
    case validationError(String)
    case notFound
    case unauthorized

    var localizedDescription: String {
        switch self {
        case .networkError(let message):
            return "Network error: \\(message)"
        case .validationError(let message):
            return "Validation error: \\(message)"
        case .notFound:
            return "Resource not found"
        case .unauthorized:
            return "Unauthorized access"
        }
    }
}
// unused_marker_67890
""",
            "UserService.swift": """// Initial
class UserService {}
""",
        },
        changed_files={
            "UserService.swift": """struct User {
    let id: String
    let name: String
}

class UserService {
    func fetchUser(id: String) throws -> User {
        guard !id.isEmpty else {
            throw AppError.validationError("ID cannot be empty")
        }

        guard let user = findUser(id: id) else {
            throw AppError.notFound
        }

        return user
    }

    func handleError(_ error: AppError) {
        switch error {
        case .networkError(let msg):
            print("Network issue: \\(msg)")
        case .validationError(let msg):
            print("Invalid input: \\(msg)")
        case .notFound:
            print("User not found")
        case .unauthorized:
            print("Please login")
        }
    }

    private func findUser(id: String) -> User? {
        return nil
    }
}
""",
        },
        must_include=["UserService", "fetchUser", "AppError"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add error handling",
    ),
]


SWIFT_GENERICS_CASES = [
    DiffTestCase(
        name="swift_339_generic_constraint",
        initial_files={
            "Repository.swift": """protocol Repository {
    associatedtype Entity
    func save(_ entity: Entity)
    func find(id: String) -> Entity?
    func delete(id: String)
}
// garbage_marker_12345
""",
            "CacheService.swift": """// Initial
class CacheService {}
""",
        },
        changed_files={
            "CacheService.swift": """class CacheService<T: Comparable & Hashable> {
    private var cache: [String: T] = [:]

    func store(_ value: T, forKey key: String) {
        cache[key] = value
    }

    func retrieve(forKey key: String) -> T? {
        return cache[key]
    }

    func process<U: Numeric>(_ items: [U]) -> U {
        return items.reduce(0, +)
    }

    func filter<C: Collection>(items: C, predicate: (C.Element) -> Bool) -> [C.Element] where C.Element: Comparable {
        return items.filter(predicate).sorted()
    }
}
""",
        },
        must_include=["CacheService", "store", "retrieve"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add generic constraints",
    ),
    DiffTestCase(
        name="swift_340_associated_type",
        initial_files={
            "Container.swift": """protocol Container {
    associatedtype Item
    var count: Int { get }
    mutating func append(_ item: Item)
    subscript(i: Int) -> Item { get }
}

protocol IterableContainer: Container {
    associatedtype Iterator: IteratorProtocol where Iterator.Element == Item
    func makeIterator() -> Iterator
}
// unused_marker_67890
""",
            "Stack.swift": """// Initial
struct Stack {}
""",
        },
        changed_files={
            "Stack.swift": """struct Stack<Element>: Container {
    typealias Item = Element

    private var items: [Element] = []

    var count: Int {
        return items.count
    }

    mutating func append(_ item: Element) {
        items.append(item)
    }

    subscript(i: Int) -> Element {
        return items[i]
    }

    mutating func push(_ item: Element) {
        items.append(item)
    }

    mutating func pop() -> Element? {
        return items.popLast()
    }
}
""",
        },
        must_include=["Stack", "Container", "append"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add associated type implementation",
    ),
]


ALL_SWIFT_CASES = (
    SWIFT_PROTOCOL_CASES
    + SWIFT_OPTIONAL_CASES
    + SWIFT_CONCURRENCY_CASES
    + SWIFT_COMBINE_CASES
    + SWIFT_SWIFTUI_CASES
    + SWIFT_DATA_CASES
    + SWIFT_ERROR_CASES
    + SWIFT_GENERICS_CASES
)


@pytest.fixture
def diff_test_runner(tmp_path):
    return DiffTestRunner(tmp_path)


@pytest.mark.parametrize("case", ALL_SWIFT_CASES, ids=lambda c: c.name)
def test_swift_diff_context(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
