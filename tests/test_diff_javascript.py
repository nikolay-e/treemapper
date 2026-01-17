import pytest

from tests.utils import DiffTestCase, DiffTestRunner


@pytest.fixture
def diff_test_runner(tmp_path):
    return DiffTestRunner(tmp_path)


JS_IMPORTS_AND_CALLS_CASES = [
    DiffTestCase(
        name="js_001_named_import_resolves_to_definition",
        initial_files={
            "utils.ts": """export function fetchUser(id: string): Promise<User> {
    return fetch(`/api/users/${id}`).then(res => res.json());
}

export function fetchPosts(userId: string): Promise<Post[]> {
    return fetch(`/api/users/${userId}/posts`).then(res => res.json());
}
""",
            "main.ts": """console.log('initial');
""",
        },
        changed_files={
            "main.ts": """import { fetchUser } from './utils';

async function main() {
    const user = await fetchUser('123');
    console.log(user);
}

main();
""",
        },
        must_include=["fetchUser", "main.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add fetchUser import and usage",
    ),
    DiffTestCase(
        name="js_002_namespace_import_includes_module",
        initial_files={
            "utils.ts": """export const VERSION = '1.0.0';

export function add(a: number, b: number): number {
    return a + b;
}

export function multiply(a: number, b: number): number {
    return a * b;
}
""",
            "main.ts": """console.log('initial');
""",
        },
        changed_files={
            "main.ts": """import * as utils from './utils';

function calculate() {
    const sum = utils.add(1, 2);
    const product = utils.multiply(3, 4);
    console.log(`Version: ${utils.VERSION}, Sum: ${sum}, Product: ${product}`);
}

calculate();
""",
        },
        must_include=["utils.add", "utils.multiply", "main.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add namespace import",
    ),
    DiffTestCase(
        name="js_003_require_destructured_exports",
        initial_files={
            "module.js": """const a = 1;
const b = 2;

module.exports = { a, b };
""",
            "main.js": """console.log('initial');
""",
        },
        changed_files={
            "main.js": """const { a, b } = require('./module');

function main() {
    console.log(a + b);
}

main();
""",
        },
        must_include=["require('./module')", "main.js"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add require with destructuring",
    ),
    DiffTestCase(
        name="js_004_reexport_traces_to_original",
        initial_files={
            "core.ts": """export function coreFunction(): void {
    console.log('core');
}
""",
            "other.ts": """export { coreFunction } from './core';
""",
            "main.ts": """console.log('initial');
""",
        },
        changed_files={
            "main.ts": """import { coreFunction } from './other';

coreFunction();
""",
        },
        must_include=["coreFunction", "main.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Import re-exported function",
    ),
    DiffTestCase(
        name="js_005_type_import_resolves_definition",
        initial_files={
            "types.ts": """export interface User {
    id: string;
    name: string;
    email: string;
}

export type UserRole = 'admin' | 'user' | 'guest';
""",
            "service.ts": """console.log('initial');
""",
        },
        changed_files={
            "service.ts": """import type { User, UserRole } from './types';

function getUser(id: string): User {
    return { id, name: 'Test', email: 'test@example.com' };
}

function checkRole(role: UserRole): boolean {
    return role === 'admin';
}
""",
        },
        must_include=["User", "UserRole", "service.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add type imports",
    ),
    DiffTestCase(
        name="js_006_dynamic_import_includes_module",
        initial_files={
            "lazy.ts": """export function heavyComputation(): number {
    let result = 0;
    for (let i = 0; i < 1000000; i++) {
        result += i;
    }
    return result;
}
""",
            "main.ts": """console.log('initial');
""",
        },
        changed_files={
            "main.ts": """async function loadModule() {
    const lazy = await import('./lazy');
    const result = lazy.heavyComputation();
    console.log(result);
}

loadModule();
""",
        },
        must_include=["import('./lazy')", "main.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add dynamic import",
    ),
    DiffTestCase(
        name="js_007_optional_chaining_definitions",
        initial_files={
            "api.ts": """export interface Response {
    data?: {
        user?: {
            name?: string;
        };
    };
}

export function fetchResponse(): Response {
    return { data: { user: { name: 'Test' } } };
}
""",
            "main.ts": """console.log('initial');
""",
        },
        changed_files={
            "main.ts": """import { fetchResponse } from './api';

function getName() {
    const response = fetchResponse();
    return response?.data?.user?.name ?? 'Unknown';
}

console.log(getName());
""",
        },
        must_include=["fetchResponse", "main.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add optional chaining",
    ),
    DiffTestCase(
        name="js_008_bracket_notation_method",
        initial_files={
            "handler.ts": """export const handlers = {
    onClick: () => console.log('clicked'),
    onHover: () => console.log('hovered'),
    onFocus: () => console.log('focused'),
};
""",
            "main.ts": """console.log('initial');
""",
        },
        changed_files={
            "main.ts": """import { handlers } from './handler';

function callHandler(name: string) {
    const method = handlers[name as keyof typeof handlers];
    if (method) {
        method();
    }
}

callHandler('onClick');
""",
        },
        must_include=["handlers", "main.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add bracket notation call",
    ),
    DiffTestCase(
        name="js_009_new_class_constructor",
        initial_files={
            "user.ts": """export class MyClass {
    private value: number;

    constructor(value: number) {
        this.value = value;
    }

    getValue(): number {
        return this.value;
    }
}
""",
            "main.ts": """console.log('initial');
""",
        },
        changed_files={
            "main.ts": """import { MyClass } from './user';

function createInstance() {
    const instance = new MyClass(42);
    return instance.getValue();
}

console.log(createInstance());
""",
        },
        must_include=["MyClass", "main.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add class instantiation",
    ),
    DiffTestCase(
        name="js_010_extends_base_class",
        initial_files={
            "base.ts": """export class BaseClass {
    protected name: string;

    constructor(name: string) {
        this.name = name;
    }

    greet(): string {
        return `Hello, ${this.name}`;
    }
}
""",
            "derived.ts": """console.log('initial');
""",
        },
        changed_files={
            "derived.ts": """import { BaseClass } from './base';

export class DerivedClass extends BaseClass {
    private age: number;

    constructor(name: string, age: number) {
        super(name);
        this.age = age;
    }

    describe(): string {
        return `${this.greet()}, I am ${this.age} years old`;
    }
}
""",
        },
        must_include=["BaseClass", "DerivedClass", "derived.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add derived class",
    ),
    DiffTestCase(
        name="js_011_implements_interface",
        initial_files={
            "interfaces.ts": """export interface Serializable {
    serialize(): string;
    deserialize(data: string): void;
}

export interface Comparable<T> {
    compareTo(other: T): number;
}
""",
            "impl.ts": """console.log('initial');
""",
        },
        changed_files={
            "impl.ts": """import { Serializable, Comparable } from './interfaces';

export class DataRecord implements Serializable, Comparable<DataRecord> {
    constructor(public id: number, public value: string) {}

    serialize(): string {
        return JSON.stringify({ id: this.id, value: this.value });
    }

    deserialize(data: string): void {
        const parsed = JSON.parse(data);
        this.id = parsed.id;
        this.value = parsed.value;
    }

    compareTo(other: DataRecord): number {
        return this.id - other.id;
    }
}
""",
        },
        must_include=["Serializable", "Comparable", "impl.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Implement interfaces",
    ),
    DiffTestCase(
        name="js_012_decorator_function",
        initial_files={
            "decorators.ts": """export function Logger(target: any, key: string, descriptor: PropertyDescriptor) {
    const original = descriptor.value;
    descriptor.value = function(...args: any[]) {
        console.log(`Calling ${key} with args:`, args);
        return original.apply(this, args);
    };
    return descriptor;
}

export function Readonly(target: any, key: string) {
    Object.defineProperty(target, key, { writable: false });
}
""",
            "service.ts": """console.log('initial');
""",
        },
        changed_files={
            "service.ts": """import { Logger } from './decorators';

export class ApiService {
    @Logger
    fetchData(url: string): Promise<any> {
        return fetch(url).then(res => res.json());
    }
}
""",
        },
        must_include=["Logger", "ApiService", "service.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add decorated method",
    ),
    DiffTestCase(
        name="js_013_object_assign_source",
        initial_files={
            "defaults.ts": """export const defaultConfig = {
    timeout: 5000,
    retries: 3,
    baseUrl: 'https://api.example.com',
};
""",
            "config.ts": """console.log('initial');
""",
        },
        changed_files={
            "config.ts": """import { defaultConfig } from './defaults';

export function createConfig(overrides: Partial<typeof defaultConfig>) {
    return Object.assign({}, defaultConfig, overrides);
}
""",
        },
        must_include=["defaultConfig", "config.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add config merger",
    ),
    DiffTestCase(
        name="js_014_array_from_iterable",
        initial_files={
            "iterator.ts": """export class NumberRange {
    constructor(private start: number, private end: number) {}

    *[Symbol.iterator]() {
        for (let i = this.start; i <= this.end; i++) {
            yield i;
        }
    }
}
""",
            "main.ts": """console.log('initial');
""",
        },
        changed_files={
            "main.ts": """import { NumberRange } from './iterator';

function getNumbers() {
    const range = new NumberRange(1, 10);
    return Array.from(range);
}

console.log(getNumbers());
""",
        },
        must_include=["NumberRange", "main.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add Array.from usage",
    ),
    DiffTestCase(
        name="js_015_for_await_async_generator",
        initial_files={
            "generator.ts": """export async function* asyncGenerator() {
    for (let i = 0; i < 5; i++) {
        await new Promise(resolve => setTimeout(resolve, 100));
        yield i;
    }
}
""",
            "consumer.ts": """console.log('initial');
""",
        },
        changed_files={
            "consumer.ts": """import { asyncGenerator } from './generator';

async function consume() {
    for await (const value of asyncGenerator()) {
        console.log(value);
    }
}

consume();
""",
        },
        must_include=["asyncGenerator", "consumer.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add async iteration",
    ),
    DiffTestCase(
        name="js_016_yield_star_generator",
        initial_files={
            "sub_generator.ts": """export function* subGenerator() {
    yield 1;
    yield 2;
    yield 3;
}
""",
            "main_generator.ts": """console.log('initial');
""",
        },
        changed_files={
            "main_generator.ts": """import { subGenerator } from './sub_generator';

export function* mainGenerator() {
    yield 0;
    yield* subGenerator();
    yield 4;
}
""",
        },
        must_include=["subGenerator", "main_generator.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add yield* delegation",
    ),
    DiffTestCase(
        name="js_017_spread_objects",
        initial_files={
            "defaults.ts": """export const defaults = {
    theme: 'light',
    language: 'en',
};

export const overrides = {
    theme: 'dark',
};
""",
            "config.ts": """console.log('initial');
""",
        },
        changed_files={
            "config.ts": """import { defaults, overrides } from './defaults';

export const config = {
    ...defaults,
    ...overrides,
    version: '1.0',
};
""",
        },
        must_include=["defaults", "overrides", "config.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add spread merge",
    ),
    DiffTestCase(
        name="js_018_proxy_handler",
        initial_files={
            "handlers.ts": """export const loggingHandler: ProxyHandler<object> = {
    get(target, prop, receiver) {
        console.log(`Getting ${String(prop)}`);
        return Reflect.get(target, prop, receiver);
    },
    set(target, prop, value, receiver) {
        console.log(`Setting ${String(prop)} = ${value}`);
        return Reflect.set(target, prop, value, receiver);
    },
};
""",
            "proxy.ts": """console.log('initial');
""",
        },
        changed_files={
            "proxy.ts": """import { loggingHandler } from './handlers';

export function createLoggingProxy<T extends object>(target: T): T {
    return new Proxy(target, loggingHandler);
}
""",
        },
        must_include=["loggingHandler", "proxy.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add proxy creation",
    ),
    DiffTestCase(
        name="js_019_reflect_get",
        initial_files={
            "accessor.ts": """export class Accessor {
    private _value: number = 0;

    get value(): number {
        return this._value;
    }

    set value(v: number) {
        this._value = v;
    }
}
""",
            "main.ts": """console.log('initial');
""",
        },
        changed_files={
            "main.ts": """import { Accessor } from './accessor';

function getValue(obj: Accessor) {
    return Reflect.get(obj, 'value');
}

const accessor = new Accessor();
console.log(getValue(accessor));
""",
        },
        must_include=["Accessor", "main.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add Reflect.get usage",
    ),
    DiffTestCase(
        name="js_020_eval_function",
        initial_files={
            "functions.ts": """export function targetFunction() {
    return 'called';
}
""",
            "main.ts": """console.log('initial');
""",
        },
        changed_files={
            "main.ts": """import { targetFunction } from './functions';

function dynamicCall() {
    const result = eval('targetFunction()');
    return result;
}

console.log(dynamicCall());
""",
        },
        must_include=["targetFunction", "main.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add eval usage",
    ),
    DiffTestCase(
        name="js_021_new_function",
        initial_files={
            "target.ts": """export function targetFn() {
    return 42;
}
""",
            "main.ts": """console.log('initial');
""",
        },
        changed_files={
            "main.ts": """import { targetFn } from './target';

function createDynamicFunction() {
    const fn = new Function('return targetFn()');
    return fn;
}

const dynamic = createDynamicFunction();
""",
        },
        must_include=["targetFn", "main.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add new Function usage",
    ),
    DiffTestCase(
        name="js_022_template_tag_function",
        initial_files={
            "tags.ts": """export function sql(strings: TemplateStringsArray, ...values: any[]) {
    let result = '';
    strings.forEach((str, i) => {
        result += str + (values[i] !== undefined ? `$${i + 1}` : '');
    });
    return { text: result, values };
}
""",
            "query.ts": """console.log('initial');
""",
        },
        changed_files={
            "query.ts": """import { sql } from './tags';

function buildQuery(userId: string) {
    const query = sql`SELECT * FROM users WHERE id = ${userId}`;
    return query;
}

console.log(buildQuery('123'));
""",
        },
        must_include=["sql", "query.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add tagged template usage",
    ),
    DiffTestCase(
        name="js_023_intl_date_format",
        initial_files={
            "locale.ts": """export const localeConfig = {
    locale: 'en-US',
    options: {
        year: 'numeric' as const,
        month: 'long' as const,
        day: 'numeric' as const,
    },
};
""",
            "formatter.ts": """console.log('initial');
""",
        },
        changed_files={
            "formatter.ts": """import { localeConfig } from './locale';

export function formatDate(date: Date): string {
    const formatter = new Intl.DateTimeFormat(localeConfig.locale, localeConfig.options);
    return formatter.format(date);
}
""",
        },
        must_include=["localeConfig", "formatter.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add Intl formatter",
    ),
    DiffTestCase(
        name="js_024_web_worker_message",
        initial_files={
            "worker.ts": """self.onmessage = function(e: MessageEvent) {
    const result = e.data * 2;
    self.postMessage(result);
};
""",
            "main.ts": """console.log('initial');
""",
        },
        changed_files={
            "main.ts": """const worker = new Worker('./worker.ts');

worker.onmessage = function(e: MessageEvent) {
    console.log('Result:', e.data);
};

worker.postMessage(21);
""",
        },
        must_include=["Worker", "main.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add worker communication",
    ),
    DiffTestCase(
        name="js_025_mixed_import_default_named",
        initial_files={
            "module.ts": """export default function defaultExport() {
    return 'default';
}

export function namedExport() {
    return 'named';
}

export const VALUE = 42;
""",
            "main.ts": """console.log('initial');
""",
        },
        changed_files={
            "main.ts": """import defaultFn, { namedExport, VALUE } from './module';

function useAll() {
    console.log(defaultFn());
    console.log(namedExport());
    console.log(VALUE);
}

useAll();
""",
        },
        must_include=["namedExport", "VALUE", "main.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add mixed imports",
    ),
]

JS_REVERSE_DEPENDENCIES_CASES = [
    DiffTestCase(
        name="js_026_exported_function_change_pulls_importers",
        initial_files={
            "utils.ts": """export function fetchUser(id: string) {
    return fetch(`/api/users/${id}`);
}
""",
            "consumer.ts": """import { fetchUser } from './utils';

async function loadUser(id: string) {
    const response = await fetchUser(id);
    return response.json();
}
""",
        },
        changed_files={
            "utils.ts": """export function fetchUser(id: string, options?: RequestInit) {
    return fetch(`/api/users/${id}`, options);
}
""",
        },
        must_include=["fetchUser", "utils.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Change fetchUser signature",
    ),
    DiffTestCase(
        name="js_027_default_export_change_pulls_importers",
        initial_files={
            "api.ts": """export default function apiClient() {
    return { get: (url: string) => fetch(url) };
}
""",
            "service.ts": """import client from './api';

export function getData(url: string) {
    return client().get(url);
}
""",
        },
        changed_files={
            "api.ts": """export default function apiClient(baseUrl = '') {
    return {
        get: (url: string) => fetch(baseUrl + url),
        post: (url: string, data: any) => fetch(baseUrl + url, {
            method: 'POST',
            body: JSON.stringify(data),
        }),
    };
}
""",
        },
        must_include=["apiClient", "api.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Extend apiClient",
    ),
    DiffTestCase(
        name="js_028_interface_change_pulls_implementers",
        initial_files={
            "interfaces.ts": """export interface Repository<T> {
    findById(id: string): Promise<T | null>;
    save(entity: T): Promise<T>;
}
""",
            "user_repo.ts": """import { Repository } from './interfaces';

interface User { id: string; name: string; }

export class UserRepository implements Repository<User> {
    async findById(id: string) {
        return { id, name: 'Test' };
    }
    async save(entity: User) {
        return entity;
    }
}
""",
        },
        changed_files={
            "interfaces.ts": """export interface Repository<T> {
    findById(id: string): Promise<T | null>;
    findAll(): Promise<T[]>;
    save(entity: T): Promise<T>;
    delete(id: string): Promise<boolean>;
}
""",
        },
        must_include=["Repository", "interfaces.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add methods to Repository interface",
    ),
    DiffTestCase(
        name="js_029_type_change_pulls_usages",
        initial_files={
            "types.ts": """export type Config = {
    apiUrl: string;
    timeout: number;
};
""",
            "app.ts": """import { Config } from './types';

function init(config: Config) {
    console.log(`Connecting to ${config.apiUrl}`);
}
""",
        },
        changed_files={
            "types.ts": """export type Config = {
    apiUrl: string;
    timeout: number;
    retries: number;
    debug?: boolean;
};
""",
        },
        must_include=["Config", "types.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Extend Config type",
    ),
    DiffTestCase(
        name="js_030_enum_change_pulls_usages",
        initial_files={
            "enums.ts": """export enum Status {
    Pending = 'PENDING',
    Active = 'ACTIVE',
    Completed = 'COMPLETED',
}
""",
            "task.ts": """import { Status } from './enums';

export class Task {
    status: Status = Status.Pending;

    complete() {
        this.status = Status.Completed;
    }
}
""",
        },
        changed_files={
            "enums.ts": """export enum Status {
    Pending = 'PENDING',
    Active = 'ACTIVE',
    Completed = 'COMPLETED',
    Cancelled = 'CANCELLED',
    OnHold = 'ON_HOLD',
}
""",
        },
        must_include=["Status", "enums.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add status values",
    ),
    DiffTestCase(
        name="js_031_react_props_change",
        initial_files={
            "types.ts": """export interface ButtonProps {
    label: string;
    onClick: () => void;
}
""",
            "Button.tsx": """import { ButtonProps } from './types';

export function Button({ label, onClick }: ButtonProps) {
    return <button onClick={onClick}>{label}</button>;
}
""",
        },
        changed_files={
            "types.ts": """export interface ButtonProps {
    label: string;
    onClick: () => void;
    disabled?: boolean;
    variant?: 'primary' | 'secondary';
}
""",
        },
        must_include=["ButtonProps", "types.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Extend ButtonProps",
    ),
    DiffTestCase(
        name="js_032_redux_action_change",
        initial_files={
            "actions.ts": """export const INCREMENT = 'INCREMENT';
export const DECREMENT = 'DECREMENT';

export const increment = () => ({ type: INCREMENT });
export const decrement = () => ({ type: DECREMENT });
""",
            "reducer.ts": """import { INCREMENT, DECREMENT } from './actions';

const initialState = { count: 0 };

export function counterReducer(state = initialState, action: any) {
    switch (action.type) {
        case INCREMENT:
            return { count: state.count + 1 };
        case DECREMENT:
            return { count: state.count - 1 };
        default:
            return state;
    }
}
""",
        },
        changed_files={
            "actions.ts": """export const INCREMENT = 'INCREMENT';
export const DECREMENT = 'DECREMENT';
export const RESET = 'RESET';
export const SET = 'SET';

export const increment = () => ({ type: INCREMENT });
export const decrement = () => ({ type: DECREMENT });
export const reset = () => ({ type: RESET });
export const setValue = (value: number) => ({ type: SET, payload: value });
""",
        },
        must_include=["RESET", "SET", "actions.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add new actions",
    ),
    DiffTestCase(
        name="js_033_zod_schema_change",
        initial_files={
            "schemas.ts": """import { z } from 'zod';

export const UserSchema = z.object({
    id: z.string(),
    name: z.string(),
    email: z.string().email(),
});

export type User = z.infer<typeof UserSchema>;
""",
            "validator.ts": """import { UserSchema, User } from './schemas';

export function validateUser(data: unknown): User {
    return UserSchema.parse(data);
}
""",
        },
        changed_files={
            "schemas.ts": """import { z } from 'zod';

export const UserSchema = z.object({
    id: z.string().uuid(),
    name: z.string().min(1).max(100),
    email: z.string().email(),
    age: z.number().int().positive().optional(),
    role: z.enum(['admin', 'user', 'guest']),
});

export type User = z.infer<typeof UserSchema>;
""",
        },
        must_include=["UserSchema", "schemas.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Extend UserSchema",
    ),
    DiffTestCase(
        name="js_034_express_route_change",
        initial_files={
            "routes.ts": """import { Router } from 'express';

export const userRouter = Router();

userRouter.get('/:id', (req, res) => {
    res.json({ id: req.params.id });
});
""",
            "middleware.ts": """import { userRouter } from './routes';

export function setupRoutes(app: any) {
    app.use('/users', userRouter);
}
""",
        },
        changed_files={
            "routes.ts": """import { Router } from 'express';

export const userRouter = Router();

userRouter.get('/:id', (req, res) => {
    res.json({ id: req.params.id });
});

userRouter.post('/', (req, res) => {
    res.status(201).json(req.body);
});

userRouter.delete('/:id', (req, res) => {
    res.status(204).send();
});
""",
        },
        must_include=["userRouter", "routes.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add POST and DELETE routes",
    ),
    DiffTestCase(
        name="js_035_graphql_resolver_change",
        initial_files={
            "resolvers.ts": """export const resolvers = {
    Query: {
        user: (_: any, { id }: { id: string }) => ({ id, name: 'Test' }),
    },
};
""",
            "schema.ts": r"""import { resolvers } from './resolvers';

export const typeDefs = \`
    type User {
        id: ID!
        name: String!
    }

    type Query {
        user(id: ID!): User
    }
\`;

export { resolvers };
""",
        },
        changed_files={
            "resolvers.ts": """export const resolvers = {
    Query: {
        user: (_: any, { id }: { id: string }) => ({ id, name: 'Test' }),
        users: () => [{ id: '1', name: 'User 1' }, { id: '2', name: 'User 2' }],
    },
    Mutation: {
        createUser: (_: any, { name }: { name: string }) => ({ id: Date.now().toString(), name }),
    },
};
""",
        },
        must_include=["resolvers", "resolvers.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add users query and createUser mutation",
    ),
    DiffTestCase(
        name="js_036_custom_hook_change",
        initial_files={
            "useCounter.ts": """import { useState } from 'react';

export function useCounter(initial = 0) {
    const [count, setCount] = useState(initial);
    const increment = () => setCount(c => c + 1);
    const decrement = () => setCount(c => c - 1);
    return { count, increment, decrement };
}
""",
            "Counter.tsx": """import { useCounter } from './useCounter';

export function Counter() {
    const { count, increment, decrement } = useCounter(0);
    return (
        <div>
            <span>{count}</span>
            <button onClick={increment}>+</button>
            <button onClick={decrement}>-</button>
        </div>
    );
}
""",
        },
        changed_files={
            "useCounter.ts": """import { useState, useCallback } from 'react';

export function useCounter(initial = 0, step = 1) {
    const [count, setCount] = useState(initial);
    const increment = useCallback(() => setCount(c => c + step), [step]);
    const decrement = useCallback(() => setCount(c => c - step), [step]);
    const reset = useCallback(() => setCount(initial), [initial]);
    return { count, increment, decrement, reset };
}
""",
        },
        must_include=["useCounter", "useCounter.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add step and reset to useCounter",
    ),
    DiffTestCase(
        name="js_037_event_emitter_change",
        initial_files={
            "emitter.ts": """import { EventEmitter } from 'events';

export const appEmitter = new EventEmitter();

export function emitUserCreated(user: { id: string; name: string }) {
    appEmitter.emit('userCreated', user);
}
""",
            "listener.ts": """import { appEmitter } from './emitter';

appEmitter.on('userCreated', (user) => {
    console.log('User created:', user);
});
""",
        },
        changed_files={
            "emitter.ts": """import { EventEmitter } from 'events';

export const appEmitter = new EventEmitter();

export function emitUserCreated(user: { id: string; name: string }) {
    appEmitter.emit('userCreated', user);
}

export function emitUserDeleted(userId: string) {
    appEmitter.emit('userDeleted', userId);
}

export function emitUserUpdated(user: { id: string; name: string }) {
    appEmitter.emit('userUpdated', user);
}
""",
        },
        must_include=["emitUserDeleted", "emitter.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add more events",
    ),
    DiffTestCase(
        name="js_038_promise_chain_change",
        initial_files={
            "api.ts": """export function fetchData(): Promise<{ data: string }> {
    return fetch('/api/data').then(res => res.json());
}
""",
            "consumer.ts": """import { fetchData } from './api';

fetchData().then(result => {
    console.log(result.data);
});
""",
        },
        changed_files={
            "api.ts": """export function fetchData(): Promise<{ data: string; metadata: { timestamp: number } }> {
    return fetch('/api/data')
        .then(res => res.json())
        .then(data => ({
            ...data,
            metadata: { timestamp: Date.now() },
        }));
}
""",
        },
        must_include=["fetchData", "api.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add metadata to fetchData",
    ),
    DiffTestCase(
        name="js_039_class_method_change",
        initial_files={
            "base.ts": """export class BaseService {
    protected log(message: string) {
        console.log(message);
    }

    process(data: string): string {
        this.log(`Processing: ${data}`);
        return data.toUpperCase();
    }
}
""",
            "derived.ts": """import { BaseService } from './base';

export class ExtendedService extends BaseService {
    process(data: string): string {
        const result = super.process(data);
        return `[Extended] ${result}`;
    }
}
""",
        },
        changed_files={
            "base.ts": """export class BaseService {
    protected log(message: string, level: 'info' | 'warn' | 'error' = 'info') {
        console[level](message);
    }

    process(data: string, options?: { prefix?: string }): string {
        this.log(`Processing: ${data}`, 'info');
        const result = data.toUpperCase();
        return options?.prefix ? `${options.prefix}${result}` : result;
    }
}
""",
        },
        must_include=["BaseService", "base.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Extend process method",
    ),
    DiffTestCase(
        name="js_040_module_augmentation",
        initial_files={
            "original.ts": """export interface User {
    id: string;
    name: string;
}

export function createUser(name: string): User {
    return { id: Date.now().toString(), name };
}
""",
            "augmentation.ts": """import { User } from './original';

declare module './original' {
    interface User {
        email?: string;
    }
}

export function createUserWithEmail(name: string, email: string): User {
    return { id: Date.now().toString(), name, email };
}
""",
        },
        changed_files={
            "augmentation.ts": """import { User } from './original';

declare module './original' {
    interface User {
        email?: string;
        role?: 'admin' | 'user';
    }
}

export function createUserWithEmail(name: string, email: string, role?: 'admin' | 'user'): User {
    return { id: Date.now().toString(), name, email, role };
}
""",
        },
        must_include=["createUserWithEmail", "augmentation.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add role to augmentation",
    ),
]

TYPESCRIPT_TYPES_CASES = [
    DiffTestCase(
        name="ts_041_intersection_type",
        initial_files={
            "types.ts": """export type Named = { name: string };
export type Aged = { age: number };
""",
            "person.ts": """console.log('initial');
""",
        },
        changed_files={
            "person.ts": """import { Named, Aged } from './types';

type Person = Named & Aged;

function createPerson(name: string, age: number): Person {
    return { name, age };
}
""",
        },
        must_include=["Named", "Aged", "person.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add intersection type",
    ),
    DiffTestCase(
        name="ts_042_union_type",
        initial_files={
            "result.ts": """export type Success<T> = { success: true; data: T };
export type Failure = { success: false; error: string };
""",
            "handler.ts": """console.log('initial');
""",
        },
        changed_files={
            "handler.ts": """import { Success, Failure } from './result';

type Result<T> = Success<T> | Failure;

function handleResult<T>(result: Result<T>) {
    if (result.success) {
        return result.data;
    }
    throw new Error(result.error);
}
""",
        },
        must_include=["Success", "Failure", "handler.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add union type",
    ),
    DiffTestCase(
        name="ts_043_keyof_type",
        initial_files={
            "config.ts": """export interface AppConfig {
    apiUrl: string;
    timeout: number;
    debug: boolean;
}
""",
            "getter.ts": """console.log('initial');
""",
        },
        changed_files={
            "getter.ts": """import { AppConfig } from './config';

type ConfigKey = keyof AppConfig;

function getConfig<K extends ConfigKey>(config: AppConfig, key: K): AppConfig[K] {
    return config[key];
}
""",
        },
        must_include=["AppConfig", "getter.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add keyof usage",
    ),
    DiffTestCase(
        name="ts_044_indexed_access_type",
        initial_files={
            "schema.ts": """export interface Schema {
    users: { id: string; name: string }[];
    posts: { id: string; title: string; content: string }[];
}
""",
            "accessor.ts": """console.log('initial');
""",
        },
        changed_files={
            "accessor.ts": """import { Schema } from './schema';

type User = Schema['users'][number];
type Post = Schema['posts'][number];

function getFirstUser(schema: Schema): User {
    return schema.users[0];
}
""",
        },
        must_include=["Schema", "accessor.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add indexed access",
    ),
    DiffTestCase(
        name="ts_045_partial_type",
        initial_files={
            "config.ts": """export interface FullConfig {
    host: string;
    port: number;
    ssl: boolean;
    timeout: number;
}
""",
            "updater.ts": """console.log('initial');
""",
        },
        changed_files={
            "updater.ts": """import { FullConfig } from './config';

function updateConfig(current: FullConfig, updates: Partial<FullConfig>): FullConfig {
    return { ...current, ...updates };
}
""",
        },
        must_include=["FullConfig", "updater.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add Partial usage",
    ),
    DiffTestCase(
        name="ts_046_required_type",
        initial_files={
            "options.ts": """export interface Options {
    name?: string;
    value?: number;
    enabled?: boolean;
}
""",
            "validator.ts": """console.log('initial');
""",
        },
        changed_files={
            "validator.ts": """import { Options } from './options';

type StrictOptions = Required<Options>;

function validate(options: StrictOptions): boolean {
    return options.name.length > 0 && options.value >= 0 && typeof options.enabled === 'boolean';
}
""",
        },
        must_include=["Options", "validator.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add Required usage",
    ),
    DiffTestCase(
        name="ts_047_pick_type",
        initial_files={
            "user.ts": """export interface User {
    id: string;
    name: string;
    email: string;
    password: string;
    createdAt: Date;
}
""",
            "dto.ts": """console.log('initial');
""",
        },
        changed_files={
            "dto.ts": """import { User } from './user';

type UserPublic = Pick<User, 'id' | 'name' | 'email'>;

function toPublic(user: User): UserPublic {
    return { id: user.id, name: user.name, email: user.email };
}
""",
        },
        must_include=["User", "dto.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add Pick usage",
    ),
    DiffTestCase(
        name="ts_048_omit_type",
        initial_files={
            "full.ts": """export interface FullRecord {
    id: string;
    name: string;
    secret: string;
    internal: boolean;
}
""",
            "public.ts": """console.log('initial');
""",
        },
        changed_files={
            "public.ts": """import { FullRecord } from './full';

type PublicRecord = Omit<FullRecord, 'secret' | 'internal'>;

function sanitize(record: FullRecord): PublicRecord {
    const { secret, internal, ...publicData } = record;
    return publicData;
}
""",
        },
        must_include=["FullRecord", "public.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add Omit usage",
    ),
    DiffTestCase(
        name="ts_049_return_type",
        initial_files={
            "factory.ts": """export function createUser(name: string, age: number) {
    return { id: Date.now().toString(), name, age, createdAt: new Date() };
}
""",
            "types.ts": """console.log('initial');
""",
        },
        changed_files={
            "types.ts": """import { createUser } from './factory';

type User = ReturnType<typeof createUser>;

function processUser(user: User) {
    console.log(`User ${user.name} created at ${user.createdAt}`);
}
""",
        },
        must_include=["createUser", "types.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add ReturnType usage",
    ),
    DiffTestCase(
        name="ts_050_parameters_type",
        initial_files={
            "api.ts": """export function fetchData(url: string, options: { method: string; headers: Record<string, string> }) {
    return fetch(url, options);
}
""",
            "wrapper.ts": """console.log('initial');
""",
        },
        changed_files={
            "wrapper.ts": """import { fetchData } from './api';

type FetchParams = Parameters<typeof fetchData>;

function wrappedFetch(...args: FetchParams) {
    console.log('Fetching:', args[0]);
    return fetchData(...args);
}
""",
        },
        must_include=["fetchData", "wrapper.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add Parameters usage",
    ),
]

REACT_VUE_ANGULAR_CASES = [
    DiffTestCase(
        name="react_061_component_with_props",
        initial_files={
            "Card.tsx": """interface CardProps {
    title: string;
    children: React.ReactNode;
}

export function Card({ title, children }: CardProps) {
    return (
        <div className="card">
            <h2>{title}</h2>
            {children}
        </div>
    );
}
""",
            "App.tsx": """console.log('initial');
""",
        },
        changed_files={
            "App.tsx": """import { Card } from './Card';

export function App() {
    return (
        <Card title="Welcome">
            <p>Hello World</p>
        </Card>
    );
}
""",
        },
        must_include=["Card", "App.tsx"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add Card usage",
    ),
    DiffTestCase(
        name="react_062_usestate_generic",
        initial_files={
            "types.ts": """export interface TodoItem {
    id: string;
    text: string;
    completed: boolean;
}
""",
            "TodoList.tsx": """console.log('initial');
""",
        },
        changed_files={
            "TodoList.tsx": """import { useState } from 'react';
import { TodoItem } from './types';

export function TodoList() {
    const [todos, setTodos] = useState<TodoItem[]>([]);

    const addTodo = (text: string) => {
        setTodos([...todos, { id: Date.now().toString(), text, completed: false }]);
    };

    return <div>{todos.map(t => <span key={t.id}>{t.text}</span>)}</div>;
}
""",
        },
        must_include=["TodoItem", "TodoList.tsx"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add useState with TodoItem type",
    ),
    DiffTestCase(
        name="react_063_usecontext",
        initial_files={
            "ThemeContext.tsx": """import { createContext } from 'react';

export interface Theme {
    primary: string;
    secondary: string;
}

export const ThemeContext = createContext<Theme>({ primary: '#000', secondary: '#fff' });
""",
            "Button.tsx": """console.log('initial');
""",
        },
        changed_files={
            "Button.tsx": """import { useContext } from 'react';
import { ThemeContext } from './ThemeContext';

export function Button({ children }: { children: React.ReactNode }) {
    const theme = useContext(ThemeContext);
    return <button style={{ backgroundColor: theme.primary }}>{children}</button>;
}
""",
        },
        must_include=["ThemeContext", "Button.tsx"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add ThemeContext usage",
    ),
    DiffTestCase(
        name="react_064_usereducer",
        initial_files={
            "reducer.ts": """export type State = { count: number };
export type Action = { type: 'increment' } | { type: 'decrement' } | { type: 'reset' };

export function counterReducer(state: State, action: Action): State {
    switch (action.type) {
        case 'increment': return { count: state.count + 1 };
        case 'decrement': return { count: state.count - 1 };
        case 'reset': return { count: 0 };
    }
}
""",
            "Counter.tsx": """console.log('initial');
""",
        },
        changed_files={
            "Counter.tsx": """import { useReducer } from 'react';
import { counterReducer, State } from './reducer';

const initialState: State = { count: 0 };

export function Counter() {
    const [state, dispatch] = useReducer(counterReducer, initialState);
    return (
        <div>
            <span>{state.count}</span>
            <button onClick={() => dispatch({ type: 'increment' })}>+</button>
        </div>
    );
}
""",
        },
        must_include=["counterReducer", "Counter.tsx"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add useReducer",
    ),
    DiffTestCase(
        name="react_065_usememo",
        initial_files={
            "compute.ts": """export function expensiveComputation(items: number[]): number {
    return items.reduce((sum, n) => sum + n * n, 0);
}
""",
            "Stats.tsx": """console.log('initial');
""",
        },
        changed_files={
            "Stats.tsx": """import { useMemo } from 'react';
import { expensiveComputation } from './compute';

export function Stats({ items }: { items: number[] }) {
    const result = useMemo(() => expensiveComputation(items), [items]);
    return <div>Result: {result}</div>;
}
""",
        },
        must_include=["expensiveComputation", "Stats.tsx"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add useMemo",
    ),
]

NODE_BACKEND_CASES = [
    DiffTestCase(
        name="node_076_express_middleware",
        initial_files={
            "authMiddleware.ts": """import { Request, Response, NextFunction } from 'express';

export function authMiddleware(req: Request, res: Response, next: NextFunction) {
    const token = req.headers.authorization;
    if (!token) {
        return res.status(401).json({ error: 'Unauthorized' });
    }
    next();
}
""",
            "app.ts": """console.log('initial');
""",
        },
        changed_files={
            "app.ts": """import express from 'express';
import { authMiddleware } from './authMiddleware';

const app = express();
app.use(authMiddleware);

app.get('/protected', (req, res) => {
    res.json({ message: 'Protected content' });
});
""",
        },
        must_include=["authMiddleware", "app.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add middleware usage",
    ),
    DiffTestCase(
        name="node_077_route_handler",
        initial_files={
            "userHandler.ts": """import { Request, Response } from 'express';

export async function getUserHandler(req: Request, res: Response) {
    const { id } = req.params;
    res.json({ id, name: 'User' });
}
""",
            "routes.ts": """console.log('initial');
""",
        },
        changed_files={
            "routes.ts": """import { Router } from 'express';
import { getUserHandler } from './userHandler';

export const router = Router();
router.get('/users/:id', getUserHandler);
""",
        },
        must_include=["getUserHandler", "routes.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add route handler",
    ),
    DiffTestCase(
        name="node_078_request_body_validation",
        initial_files={
            "schemas.ts": """export interface CreateUserBody {
    name: string;
    email: string;
    password: string;
}
""",
            "controller.ts": """console.log('initial');
""",
        },
        changed_files={
            "controller.ts": """import { Request, Response } from 'express';
import { CreateUserBody } from './schemas';

export function createUser(req: Request, res: Response) {
    const body = req.body as CreateUserBody;
    res.status(201).json({ id: '1', name: body.name, email: body.email });
}
""",
        },
        must_include=["CreateUserBody", "controller.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add body validation",
    ),
    DiffTestCase(
        name="node_079_response_json",
        initial_files={
            "service.ts": """export interface ApiResponse<T> {
    data: T;
    success: boolean;
    timestamp: number;
}

export function createResponse<T>(data: T): ApiResponse<T> {
    return { data, success: true, timestamp: Date.now() };
}
""",
            "handler.ts": """console.log('initial');
""",
        },
        changed_files={
            "handler.ts": """import { Request, Response } from 'express';
import { createResponse } from './service';

export function getDataHandler(req: Request, res: Response) {
    const data = { message: 'Hello' };
    res.json(createResponse(data));
}
""",
        },
        must_include=["createResponse", "handler.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add response helper",
    ),
    DiffTestCase(
        name="node_080_socket_event",
        initial_files={
            "events.ts": """export interface ChatMessage {
    userId: string;
    text: string;
    timestamp: number;
}

export const CHAT_EVENT = 'chat:message';
""",
            "socket.ts": """console.log('initial');
""",
        },
        changed_files={
            "socket.ts": """import { Server } from 'socket.io';
import { CHAT_EVENT, ChatMessage } from './events';

export function setupSocket(io: Server) {
    io.on('connection', (socket) => {
        socket.on(CHAT_EVENT, (message: ChatMessage) => {
            io.emit(CHAT_EVENT, message);
        });
    });
}
""",
        },
        must_include=["CHAT_EVENT", "socket.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add socket handler",
    ),
]

JS_TEST_FRAMEWORKS_CASES = [
    DiffTestCase(
        name="jest_091_describe_module",
        initial_files={
            "calculator.ts": """export function add(a: number, b: number): number {
    return a + b;
}

export function multiply(a: number, b: number): number {
    return a * b;
}
""",
            "calculator.test.ts": """console.log('initial');
""",
        },
        changed_files={
            "calculator.test.ts": """import { add, multiply } from './calculator';

describe('Calculator', () => {
    describe('add', () => {
        it('should add two numbers', () => {
            expect(add(1, 2)).toBe(3);
        });
    });

    describe('multiply', () => {
        it('should multiply two numbers', () => {
            expect(multiply(2, 3)).toBe(6);
        });
    });
});
""",
        },
        must_include=["add", "multiply", "calculator.test.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add calculator tests",
    ),
    DiffTestCase(
        name="jest_092_it_calls_function",
        initial_files={
            "validator.ts": r"""export function isValidEmail(email: string): boolean {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
""",
            "validator.test.ts": """console.log('initial');
""",
        },
        changed_files={
            "validator.test.ts": """import { isValidEmail } from './validator';

describe('Validator', () => {
    it('should validate correct email', () => {
        expect(isValidEmail('test@example.com')).toBe(true);
    });

    it('should reject invalid email', () => {
        expect(isValidEmail('invalid')).toBe(false);
    });
});
""",
        },
        must_include=["isValidEmail", "validator.test.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add validator tests",
    ),
    DiffTestCase(
        name="jest_093_mock_module",
        initial_files={
            "api.ts": """export async function fetchUser(id: string) {
    const response = await fetch(`/api/users/${id}`);
    return response.json();
}
""",
            "service.ts": """import { fetchUser } from './api';

export async function getUserName(id: string): Promise<string> {
    const user = await fetchUser(id);
    return user.name;
}
""",
            "service.test.ts": """console.log('initial');
""",
        },
        changed_files={
            "service.test.ts": """import { getUserName } from './service';
import { fetchUser } from './api';

jest.mock('./api');

const mockedFetchUser = fetchUser as jest.MockedFunction<typeof fetchUser>;

describe('Service', () => {
    it('should return user name', async () => {
        mockedFetchUser.mockResolvedValue({ id: '1', name: 'Test User' });
        const name = await getUserName('1');
        expect(name).toBe('Test User');
    });
});
""",
        },
        must_include=["getUserName", "service.test.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add service tests with mock",
    ),
    DiffTestCase(
        name="jest_094_spy_on_method",
        initial_files={
            "logger.ts": """export const logger = {
    log: (message: string) => console.log(message),
    error: (message: string) => console.error(message),
};
""",
            "app.ts": """import { logger } from './logger';

export function processData(data: string) {
    logger.log(`Processing: ${data}`);
    return data.toUpperCase();
}
""",
            "app.test.ts": """console.log('initial');
""",
        },
        changed_files={
            "app.test.ts": """import { processData } from './app';
import { logger } from './logger';

describe('App', () => {
    it('should log when processing', () => {
        const spy = jest.spyOn(logger, 'log');
        processData('test');
        expect(spy).toHaveBeenCalledWith('Processing: test');
        spy.mockRestore();
    });
});
""",
        },
        must_include=["processData", "app.test.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add app tests with spy",
    ),
    DiffTestCase(
        name="vitest_095_vi_fn",
        initial_files={
            "callback.ts": """export type Callback = (value: number) => void;

export function processNumbers(numbers: number[], callback: Callback) {
    numbers.forEach(n => callback(n));
}
""",
            "callback.test.ts": """console.log('initial');
""",
        },
        changed_files={
            "callback.test.ts": """import { describe, it, expect, vi } from 'vitest';
import { processNumbers } from './callback';

describe('processNumbers', () => {
    it('should call callback for each number', () => {
        const callback = vi.fn();
        processNumbers([1, 2, 3], callback);
        expect(callback).toHaveBeenCalledTimes(3);
        expect(callback).toHaveBeenCalledWith(1);
        expect(callback).toHaveBeenCalledWith(2);
        expect(callback).toHaveBeenCalledWith(3);
    });
});
""",
        },
        must_include=["processNumbers", "callback.test.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add vitest tests",
    ),
    DiffTestCase(
        name="jest_096_expect_called_with",
        initial_files={
            "notifier.ts": """export interface Notification {
    title: string;
    body: string;
}

export function sendNotification(notify: (n: Notification) => void, title: string, body: string) {
    notify({ title, body });
}
""",
            "notifier.test.ts": """console.log('initial');
""",
        },
        changed_files={
            "notifier.test.ts": """import { sendNotification, Notification } from './notifier';

describe('sendNotification', () => {
    it('should call notify with correct args', () => {
        const notify = jest.fn<void, [Notification]>();
        sendNotification(notify, 'Hello', 'World');
        expect(notify).toHaveBeenCalledWith({ title: 'Hello', body: 'World' });
    });
});
""",
        },
        must_include=["sendNotification", "notifier.test.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add notifier tests",
    ),
    DiffTestCase(
        name="testing_library_097_render",
        initial_files={
            "Greeting.tsx": """interface GreetingProps {
    name: string;
}

export function Greeting({ name }: GreetingProps) {
    return <h1>Hello, {name}!</h1>;
}
""",
            "Greeting.test.tsx": """console.log('initial');
""",
        },
        changed_files={
            "Greeting.test.tsx": """import { render, screen } from '@testing-library/react';
import { Greeting } from './Greeting';

describe('Greeting', () => {
    it('should display name', () => {
        render(<Greeting name="World" />);
        expect(screen.getByText('Hello, World!')).toBeInTheDocument();
    });
});
""",
        },
        must_include=["Greeting", "Greeting.test.tsx"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add Greeting tests",
    ),
    DiffTestCase(
        name="playwright_098_page_click",
        initial_files={
            "login.ts": """export function getLoginUrl(): string {
    return '/login';
}

export function getCredentials() {
    return { username: 'test', password: 'test123' };  // pragma: allowlist secret
}
""",
            "login.spec.ts": """console.log('initial');
""",
        },
        changed_files={
            "login.spec.ts": """import { test, expect } from '@playwright/test';
import { getLoginUrl, getCredentials } from './login';

test('user can log in', async ({ page }) => {
    await page.goto(getLoginUrl());
    const { username, password } = getCredentials();
    await page.fill('[name=username]', username);
    await page.fill('[name=password]', password);
    await page.click('button[type=submit]');
    await expect(page).toHaveURL('/dashboard');
});
""",
        },
        must_include=["getLoginUrl", "login.spec.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add login e2e test",
    ),
    DiffTestCase(
        name="cypress_099_cy_get",
        initial_files={
            "form.ts": """export const FORM_SELECTORS = {
    nameInput: '[data-testid=name-input]',
    emailInput: '[data-testid=email-input]',
    submitButton: '[data-testid=submit-btn]',
};
""",
            "form.cy.ts": """console.log('initial');
""",
        },
        changed_files={
            "form.cy.ts": """import { FORM_SELECTORS } from './form';

describe('Contact Form', () => {
    it('should submit form', () => {
        cy.visit('/contact');
        cy.get(FORM_SELECTORS.nameInput).type('John Doe');
        cy.get(FORM_SELECTORS.emailInput).type('john@example.com');
        cy.get(FORM_SELECTORS.submitButton).click();
        cy.contains('Thank you').should('be.visible');
    });
});
""",
        },
        must_include=["FORM_SELECTORS", "form.cy.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add cypress form test",
    ),
    DiffTestCase(
        name="storybook_100_story",
        initial_files={
            "Button.tsx": """export interface ButtonProps {
    label: string;
    variant?: 'primary' | 'secondary';
    size?: 'small' | 'medium' | 'large';
    onClick?: () => void;
}

export function Button({ label, variant = 'primary', size = 'medium', onClick }: ButtonProps) {
    return (
        <button className={`btn btn-${variant} btn-${size}`} onClick={onClick}>
            {label}
        </button>
    );
}
""",
            "Button.stories.tsx": """console.log('initial');
""",
        },
        changed_files={
            "Button.stories.tsx": """import type { Meta, StoryObj } from '@storybook/react';
import { Button, ButtonProps } from './Button';

const meta: Meta<typeof Button> = {
    title: 'Components/Button',
    component: Button,
    argTypes: {
        variant: { control: 'select', options: ['primary', 'secondary'] },
        size: { control: 'select', options: ['small', 'medium', 'large'] },
    },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
    args: {
        label: 'Primary Button',
        variant: 'primary',
    },
};

export const Secondary: Story = {
    args: {
        label: 'Secondary Button',
        variant: 'secondary',
    },
};
""",
        },
        must_include=["Button", "Button.stories.tsx"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add Button storybook",
    ),
]

REACT_ADVANCED_CASES = [
    DiffTestCase(
        name="react_066_custom_hook",
        initial_files={
            "useApi.ts": """import { useState, useEffect } from 'react';

export function useApi<T>(url: string) {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        fetch(url)
            .then(res => res.json())
            .then(setData)
            .catch(setError)
            .finally(() => setLoading(false));
    }, [url]);

    return { data, loading, error };
}
""",
            "UserList.tsx": """console.log('initial');
""",
        },
        changed_files={
            "UserList.tsx": """import { useApi } from './useApi';

interface User {
    id: string;
    name: string;
}

export function UserList() {
    const { data, loading, error } = useApi<User[]>('/api/users');
    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error.message}</div>;
    return <ul>{data?.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}
""",
        },
        must_include=["useApi", "UserList.tsx"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add useApi hook usage",
    ),
    DiffTestCase(
        name="react_067_forward_ref",
        initial_files={
            "Input.tsx": """import { forwardRef } from 'react';

interface InputProps {
    label: string;
    type?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ label, type = 'text' }, ref) => (
        <div>
            <label>{label}</label>
            <input ref={ref} type={type} />
        </div>
    )
);
""",
            "Form.tsx": """console.log('initial');
""",
        },
        changed_files={
            "Form.tsx": """import { useRef } from 'react';
import { Input } from './Input';

export function Form() {
    const emailRef = useRef<HTMLInputElement>(null);

    const handleSubmit = () => {
        emailRef.current?.focus();
    };

    return (
        <form onSubmit={handleSubmit}>
            <Input ref={emailRef} label="Email" type="email" />
        </form>
    );
}
""",
        },
        must_include=["Input", "Form.tsx"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add forwardRef usage",
    ),
    DiffTestCase(
        name="react_068_react_memo",
        initial_files={
            "ExpensiveList.tsx": """import { memo } from 'react';

interface Item {
    id: string;
    name: string;
}

interface ExpensiveListProps {
    items: Item[];
}

function ExpensiveListComponent({ items }: ExpensiveListProps) {
    return (
        <ul>
            {items.map(item => (
                <li key={item.id}>{item.name}</li>
            ))}
        </ul>
    );
}

export const ExpensiveList = memo(ExpensiveListComponent);
""",
            "Dashboard.tsx": """console.log('initial');
""",
        },
        changed_files={
            "Dashboard.tsx": """import { useState } from 'react';
import { ExpensiveList } from './ExpensiveList';

export function Dashboard() {
    const [items] = useState([{ id: '1', name: 'Item 1' }]);
    const [count, setCount] = useState(0);

    return (
        <div>
            <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
            <ExpensiveList items={items} />
        </div>
    );
}
""",
        },
        must_include=["ExpensiveList", "Dashboard.tsx"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add memoized component usage",
    ),
    DiffTestCase(
        name="react_069_use_callback",
        initial_files={
            "handlers.ts": """export function createClickHandler(id: string) {
    return () => console.log('Clicked:', id);
}
""",
            "ActionButton.tsx": """console.log('initial');
""",
        },
        changed_files={
            "ActionButton.tsx": """import { useCallback } from 'react';
import { createClickHandler } from './handlers';

export function ActionButton({ id }: { id: string }) {
    const handleClick = useCallback(() => {
        createClickHandler(id)();
    }, [id]);

    return <button onClick={handleClick}>Action</button>;
}
""",
        },
        must_include=["createClickHandler", "ActionButton.tsx"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add useCallback",
    ),
    DiffTestCase(
        name="react_070_redux_action",
        initial_files={
            "userSlice.ts": """import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface User {
    id: string;
    name: string;
}

interface UserState {
    users: User[];
    loading: boolean;
}

const initialState: UserState = { users: [], loading: false };

export const userSlice = createSlice({
    name: 'users',
    initialState,
    reducers: {
        addUser: (state, action: PayloadAction<User>) => {
            state.users.push(action.payload);
        },
        removeUser: (state, action: PayloadAction<string>) => {
            state.users = state.users.filter(u => u.id !== action.payload);
        },
    },
});

export const { addUser, removeUser } = userSlice.actions;
""",
            "UserForm.tsx": """console.log('initial');
""",
        },
        changed_files={
            "UserForm.tsx": """import { useDispatch } from 'react-redux';
import { addUser } from './userSlice';

export function UserForm() {
    const dispatch = useDispatch();

    const handleAdd = () => {
        dispatch(addUser({ id: Date.now().toString(), name: 'New User' }));
    };

    return <button onClick={handleAdd}>Add User</button>;
}
""",
        },
        must_include=["addUser", "UserForm.tsx"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add Redux action dispatch",
    ),
]

VUE_PATTERNS_CASES = [
    DiffTestCase(
        name="vue_071_reactive_ref",
        initial_files={
            "Counter.vue": """<script setup lang="ts">
import { ref } from 'vue';

const count = ref(0);

function increment() {
    count.value++;
}
</script>

<template>
    <button @click="increment">{{ count }}</button>
</template>
""",
            "App.vue": """<template><div>initial</div></template>
""",
        },
        changed_files={
            "App.vue": """<script setup lang="ts">
import Counter from './Counter.vue';
</script>

<template>
    <div>
        <h1>App</h1>
        <Counter />
    </div>
</template>
""",
        },
        must_include=["Counter", "App.vue"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add Counter component",
    ),
    DiffTestCase(
        name="vue_072_computed",
        initial_files={
            "utils.ts": """export function formatName(first: string, last: string): string {
    return `${first} ${last}`;
}
""",
            "Profile.vue": """<template><div>initial</div></template>
""",
        },
        changed_files={
            "Profile.vue": """<script setup lang="ts">
import { ref, computed } from 'vue';
import { formatName } from './utils';

const firstName = ref('John');
const lastName = ref('Doe');

const fullName = computed(() => formatName(firstName.value, lastName.value));
</script>

<template>
    <div>{{ fullName }}</div>
</template>
""",
        },
        must_include=["formatName", "Profile.vue"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add computed property",
    ),
    DiffTestCase(
        name="vue_073_watch",
        initial_files={
            "api.ts": """export async function fetchUserData(userId: string) {
    return { id: userId, name: 'User' };
}
""",
            "UserDetails.vue": """<template><div>initial</div></template>
""",
        },
        changed_files={
            "UserDetails.vue": """<script setup lang="ts">
import { ref, watch } from 'vue';
import { fetchUserData } from './api';

const props = defineProps<{ userId: string }>();
const userData = ref<{ id: string; name: string } | null>(null);

watch(() => props.userId, async (newId) => {
    userData.value = await fetchUserData(newId);
}, { immediate: true });
</script>

<template>
    <div v-if="userData">{{ userData.name }}</div>
</template>
""",
        },
        must_include=["fetchUserData", "UserDetails.vue"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add watch effect",
    ),
    DiffTestCase(
        name="vue_074_define_props",
        initial_files={
            "types.ts": """export interface CardProps {
    title: string;
    subtitle?: string;
    variant: 'primary' | 'secondary';
}
""",
            "Card.vue": """<template><div>initial</div></template>
""",
        },
        changed_files={
            "Card.vue": """<script setup lang="ts">
import type { CardProps } from './types';

const props = defineProps<CardProps>();
</script>

<template>
    <div :class="props.variant">
        <h2>{{ props.title }}</h2>
        <p v-if="props.subtitle">{{ props.subtitle }}</p>
    </div>
</template>
""",
        },
        must_include=["CardProps", "Card.vue"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add defineProps with type",
    ),
    DiffTestCase(
        name="vue_075_define_emits",
        initial_files={
            "events.ts": """export interface FormEvents {
    submit: [data: { name: string; email: string }];
    cancel: [];
}
""",
            "ContactForm.vue": """<template><div>initial</div></template>
""",
        },
        changed_files={
            "ContactForm.vue": """<script setup lang="ts">
import { ref } from 'vue';
import type { FormEvents } from './events';

const name = ref('');
const email = ref('');

const emit = defineEmits<FormEvents>();

function handleSubmit() {
    emit('submit', { name: name.value, email: email.value });
}
</script>

<template>
    <form @submit.prevent="handleSubmit">
        <input v-model="name" />
        <input v-model="email" />
        <button type="submit">Submit</button>
        <button type="button" @click="emit('cancel')">Cancel</button>
    </form>
</template>
""",
        },
        must_include=["FormEvents", "ContactForm.vue"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add defineEmits with type",
    ),
]

ANGULAR_PATTERNS_CASES = [
    DiffTestCase(
        name="angular_076_input_decorator",
        initial_files={
            "user.model.ts": """export interface User {
    id: string;
    name: string;
    email: string;
}
""",
            "user-card.component.ts": """console.log('initial');
""",
        },
        changed_files={
            "user-card.component.ts": """import { Component, Input } from '@angular/core';
import { User } from './user.model';

@Component({
    selector: 'app-user-card',
    template: `
        <div class="card">
            <h3>{{ user.name }}</h3>
            <p>{{ user.email }}</p>
        </div>
    `
})
export class UserCardComponent {
    @Input() user!: User;
}
""",
        },
        must_include=["User", "user-card.component.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add @Input decorator",
    ),
    DiffTestCase(
        name="angular_077_output_decorator",
        initial_files={
            "item.model.ts": """export interface Item {
    id: string;
    name: string;
}
""",
            "item-row.component.ts": """console.log('initial');
""",
        },
        changed_files={
            "item-row.component.ts": """import { Component, Input, Output, EventEmitter } from '@angular/core';
import { Item } from './item.model';

@Component({
    selector: 'app-item-row',
    template: `
        <div class="row">
            <span>{{ item.name }}</span>
            <button (click)="onDelete()">Delete</button>
        </div>
    `
})
export class ItemRowComponent {
    @Input() item!: Item;
    @Output() deleted = new EventEmitter<string>();

    onDelete() {
        this.deleted.emit(this.item.id);
    }
}
""",
        },
        must_include=["Item", "item-row.component.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add @Output decorator",
    ),
    DiffTestCase(
        name="angular_078_service_injection",
        initial_files={
            "user.service.ts": """import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

interface User {
    id: string;
    name: string;
}

@Injectable({ providedIn: 'root' })
export class UserService {
    constructor(private http: HttpClient) {}

    getUsers(): Observable<User[]> {
        return this.http.get<User[]>('/api/users');
    }
}
""",
            "user-list.component.ts": """console.log('initial');
""",
        },
        changed_files={
            "user-list.component.ts": """import { Component, OnInit } from '@angular/core';
import { UserService } from './user.service';

@Component({
    selector: 'app-user-list',
    template: `
        <ul>
            <li *ngFor="let user of users">{{ user.name }}</li>
        </ul>
    `
})
export class UserListComponent implements OnInit {
    users: any[] = [];

    constructor(private userService: UserService) {}

    ngOnInit() {
        this.userService.getUsers().subscribe(users => this.users = users);
    }
}
""",
        },
        must_include=["UserService", "user-list.component.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add service injection",
    ),
    DiffTestCase(
        name="angular_079_http_client",
        initial_files={
            "api.config.ts": """export const API_BASE = '/api';

export interface ApiResponse<T> {
    data: T;
    status: number;
}
""",
            "data.service.ts": """console.log('initial');
""",
        },
        changed_files={
            "data.service.ts": """import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { API_BASE, ApiResponse } from './api.config';

@Injectable({ providedIn: 'root' })
export class DataService {
    constructor(private http: HttpClient) {}

    getData<T>(endpoint: string): Observable<T> {
        return this.http.get<ApiResponse<T>>(`${API_BASE}${endpoint}`)
            .pipe(map(response => response.data));
    }
}
""",
        },
        must_include=["API_BASE", "data.service.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add HttpClient usage",
    ),
    DiffTestCase(
        name="angular_080_observable_pipe",
        initial_files={
            "transformers.ts": """export function filterActive<T extends { active: boolean }>(items: T[]): T[] {
    return items.filter(item => item.active);
}
""",
            "list.component.ts": """console.log('initial');
""",
        },
        changed_files={
            "list.component.ts": """import { Component } from '@angular/core';
import { Observable, of } from 'rxjs';
import { map } from 'rxjs/operators';
import { filterActive } from './transformers';

interface Item {
    id: string;
    name: string;
    active: boolean;
}

@Component({
    selector: 'app-list',
    template: `<div *ngFor="let item of items$ | async">{{ item.name }}</div>`
})
export class ListComponent {
    items$: Observable<Item[]> = of([
        { id: '1', name: 'Item 1', active: true },
        { id: '2', name: 'Item 2', active: false },
    ]).pipe(map(filterActive));
}
""",
        },
        must_include=["filterActive", "list.component.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Add Observable pipe",
    ),
]

ALL_JS_TEST_CASES = (
    JS_IMPORTS_AND_CALLS_CASES
    + JS_REVERSE_DEPENDENCIES_CASES
    + TYPESCRIPT_TYPES_CASES
    + REACT_VUE_ANGULAR_CASES
    + NODE_BACKEND_CASES
    + JS_TEST_FRAMEWORKS_CASES
    + REACT_ADVANCED_CASES
    + VUE_PATTERNS_CASES
    + ANGULAR_PATTERNS_CASES
)


@pytest.mark.parametrize("case", ALL_JS_TEST_CASES, ids=lambda c: c.name)
def test_javascript_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
