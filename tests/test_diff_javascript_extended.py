import pytest

from tests.utils import DiffTestCase, DiffTestRunner

JS_REVERSE_DEPENDENCY_CASES = [
    DiffTestCase(
        name="js_001_exported_function_change",
        initial_files={
            "utils.ts": """export function fetchUser(id: string) {
    return fetch(`/api/users/${id}`);
}

// js_garbage_marker_001
function unusedHelperFunction() {
    return "should not appear";
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

// js_garbage_marker_001
function unusedHelperFunction() {
    return "should not appear";
}
""",
        },
        must_include=["utils.ts"],
        must_not_include=["js_garbage_marker_001"],
        commit_message="Change fetchUser signature",
    ),
    DiffTestCase(
        name="js_002_default_export_change",
        initial_files={
            "api.ts": """export default function apiClient() {
    return { get: (url: string) => fetch(url) };
}

// js_garbage_marker_002
const UNUSED_CONFIG = { timeout: 5000 };
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

// js_garbage_marker_002
const UNUSED_CONFIG = { timeout: 5000 };
""",
        },
        must_include=["api.ts"],
        must_not_include=["js_garbage_marker_002"],
        commit_message="Extend apiClient",
    ),
    DiffTestCase(
        name="js_003_interface_change",
        initial_files={
            "interfaces.ts": """export interface Repository<T> {
    findById(id: string): Promise<T | null>;
    save(entity: T): Promise<T>;
}

// js_garbage_marker_003
interface UnusedInterface { unused: boolean }
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

// js_garbage_marker_003
interface UnusedInterface { unused: boolean }
""",
        },
        must_include=["interfaces.ts"],
        must_not_include=["js_garbage_marker_003"],
        commit_message="Add methods to Repository interface",
    ),
    DiffTestCase(
        name="js_004_type_change",
        initial_files={
            "types.ts": """export type Config = {
    apiUrl: string;
    timeout: number;
};

// js_garbage_marker_004
type UnusedType = { garbage: true };
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

// js_garbage_marker_004
type UnusedType = { garbage: true };
""",
        },
        must_include=["types.ts"],
        must_not_include=["js_garbage_marker_004"],
        commit_message="Extend Config type",
    ),
    DiffTestCase(
        name="js_005_enum_change",
        initial_files={
            "enums.ts": """export enum Status {
    Pending = 'PENDING',
    Active = 'ACTIVE',
    Completed = 'COMPLETED',
}

// js_garbage_marker_005
const GARBAGE_ENUM_CONFIG = { unused: true };
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

// js_garbage_marker_005
const GARBAGE_ENUM_CONFIG = { unused: true };
""",
        },
        must_include=["enums.ts"],
        must_not_include=["js_garbage_marker_005"],
        commit_message="Add status values",
    ),
    DiffTestCase(
        name="js_006_react_props_change",
        initial_files={
            "types.ts": """export interface ButtonProps {
    label: string;
    onClick: () => void;
}

// js_garbage_marker_006
const GARBAGE_BUTTON_CONFIG = { maxWidth: 200 };
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

// js_garbage_marker_006
const GARBAGE_BUTTON_CONFIG = { maxWidth: 200 };
""",
        },
        must_include=["types.ts"],
        must_not_include=["js_garbage_marker_006"],
        commit_message="Extend ButtonProps",
    ),
    DiffTestCase(
        name="js_007_redux_action_change",
        initial_files={
            "actions.ts": """export const INCREMENT = 'INCREMENT';
export const DECREMENT = 'DECREMENT';

export const increment = () => ({ type: INCREMENT });
export const decrement = () => ({ type: DECREMENT });

// js_garbage_marker_007
const GARBAGE_ACTION = 'GARBAGE';
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

// js_garbage_marker_007
const GARBAGE_ACTION = 'GARBAGE';
""",
        },
        must_include=["actions.ts"],
        must_not_include=["js_garbage_marker_007"],
        commit_message="Add new actions",
    ),
    DiffTestCase(
        name="js_008_zod_schema_change",
        initial_files={
            "schemas.ts": """import { z } from 'zod';

export const UserSchema = z.object({
    id: z.string(),
    name: z.string(),
    email: z.string().email(),
});

export type User = z.infer<typeof UserSchema>;

// js_garbage_marker_008
const GARBAGE_SCHEMA = z.object({ garbage: z.boolean() });
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

// js_garbage_marker_008
const GARBAGE_SCHEMA = z.object({ garbage: z.boolean() });
""",
        },
        must_include=["schemas.ts"],
        must_not_include=["js_garbage_marker_008"],
        commit_message="Extend UserSchema",
    ),
    DiffTestCase(
        name="js_009_express_route_change",
        initial_files={
            "routes.ts": """import { Router } from 'express';

export const userRouter = Router();

userRouter.get('/:id', (req, res) => {
    res.json({ id: req.params.id });
});

// js_garbage_marker_009
const GARBAGE_ROUTE = '/garbage';
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

// js_garbage_marker_009
const GARBAGE_ROUTE = '/garbage';
""",
        },
        must_include=["routes.ts"],
        must_not_include=["js_garbage_marker_009"],
        commit_message="Add POST and DELETE routes",
    ),
    DiffTestCase(
        name="js_010_graphql_resolver_change",
        initial_files={
            "resolvers.ts": r"""export const resolvers = {
    Query: {
        user: (_: any, { id }: { id: string }) => ({ id, name: 'Test' }),
    },
};

// js_garbage_marker_010
const GARBAGE_RESOLVER = { garbage: () => null };
""",
            "schema.ts": r"""import { resolvers } from './resolvers';

export const typeDefs = `
    type User {
        id: ID!
        name: String!
    }

    type Query {
        user(id: ID!): User
    }
`;

export { resolvers };
""",
        },
        changed_files={
            "resolvers.ts": r"""export const resolvers = {
    Query: {
        user: (_: any, { id }: { id: string }) => ({ id, name: 'Test' }),
        users: () => [{ id: '1', name: 'User 1' }, { id: '2', name: 'User 2' }],
    },
    Mutation: {
        createUser: (_: any, { name }: { name: string }) => ({ id: Date.now().toString(), name }),
    },
};

// js_garbage_marker_010
const GARBAGE_RESOLVER = { garbage: () => null };
""",
        },
        must_include=["resolvers.ts"],
        must_not_include=["js_garbage_marker_010"],
        commit_message="Add users query and createUser mutation",
    ),
    DiffTestCase(
        name="js_011_custom_hook_change",
        initial_files={
            "useCounter.ts": """import { useState } from 'react';

export function useCounter(initial = 0) {
    const [count, setCount] = useState(initial);
    const increment = () => setCount(c => c + 1);
    const decrement = () => setCount(c => c - 1);
    return { count, increment, decrement };
}

// js_garbage_marker_011
const GARBAGE_HOOK_CONFIG = { maxCount: 100 };
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

// js_garbage_marker_011
const GARBAGE_HOOK_CONFIG = { maxCount: 100 };
""",
        },
        must_include=["useCounter.ts"],
        must_not_include=["js_garbage_marker_011"],
        commit_message="Add step and reset to useCounter",
    ),
    DiffTestCase(
        name="js_012_event_emitter_change",
        initial_files={
            "emitter.ts": """import { EventEmitter } from 'events';

export const appEmitter = new EventEmitter();

export function emitUserCreated(user: { id: string; name: string }) {
    appEmitter.emit('userCreated', user);
}

// js_garbage_marker_012
const GARBAGE_EVENT = 'garbage_event';
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

// js_garbage_marker_012
const GARBAGE_EVENT = 'garbage_event';
""",
        },
        must_include=["emitter.ts"],
        must_not_include=["js_garbage_marker_012"],
        commit_message="Add more events",
    ),
    DiffTestCase(
        name="js_013_promise_chain_change",
        initial_files={
            "api.ts": """export function fetchData(): Promise<{ data: string }> {
    return fetch('/api/data').then(res => res.json());
}

// js_garbage_marker_013
function garbageApiFunction() { return Promise.resolve(null); }
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

// js_garbage_marker_013
function garbageApiFunction() { return Promise.resolve(null); }
""",
        },
        must_include=["api.ts"],
        must_not_include=["js_garbage_marker_013"],
        commit_message="Add metadata to fetchData",
    ),
    DiffTestCase(
        name="js_014_class_method_change",
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

// js_garbage_marker_014
class GarbageService { garbage() { return null; } }
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

// js_garbage_marker_014
class GarbageService { garbage() { return null; } }
""",
        },
        must_include=["base.ts"],
        must_not_include=["js_garbage_marker_014"],
        commit_message="Extend process method",
    ),
    DiffTestCase(
        name="js_015_module_augmentation",
        initial_files={
            "original.ts": """export interface User {
    id: string;
    name: string;
}

export function createUser(name: string): User {
    return { id: Date.now().toString(), name };
}

// js_garbage_marker_015
const GARBAGE_USER = { id: 'garbage', name: 'garbage' };
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
        must_include=["augmentation.ts"],
        must_not_include=["js_garbage_marker_015"],
        commit_message="Add role to augmentation",
    ),
]

TS_TYPE_CASES = [
    DiffTestCase(
        name="ts_ext_001_intersection_type",
        initial_files={
            "types.ts": """export type Named = { name: string };
export type Aged = { age: number };

// ts_ext_garbage_marker_001
type GarbageType = { garbage: boolean };
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
        must_include=["person.ts"],
        must_not_include=["ts_ext_garbage_marker_001"],
        commit_message="Add intersection type",
    ),
    DiffTestCase(
        name="ts_ext_002_union_type",
        initial_files={
            "result.ts": """export type Success<T> = { success: true; data: T };
export type Failure = { success: false; error: string };

// ts_ext_garbage_marker_002
type GarbageResult = { garbage: true };
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
        must_include=["handler.ts"],
        must_not_include=["ts_ext_garbage_marker_002"],
        commit_message="Add union type",
    ),
    DiffTestCase(
        name="ts_ext_003_keyof_type",
        initial_files={
            "config.ts": """export interface AppConfig {
    apiUrl: string;
    timeout: number;
    debug: boolean;
}

// ts_ext_garbage_marker_003
interface GarbageConfig { garbage: string }
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
        must_include=["getter.ts"],
        must_not_include=["ts_ext_garbage_marker_003"],
        commit_message="Add keyof usage",
    ),
    DiffTestCase(
        name="ts_ext_004_indexed_access_type",
        initial_files={
            "schema.ts": """export interface Schema {
    users: { id: string; name: string }[];
    posts: { id: string; title: string; content: string }[];
}

// ts_ext_garbage_marker_004
interface GarbageSchema { garbage: unknown[] }
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
        must_include=["accessor.ts"],
        must_not_include=["ts_ext_garbage_marker_004"],
        commit_message="Add indexed access",
    ),
    DiffTestCase(
        name="ts_ext_005_partial_type",
        initial_files={
            "config.ts": """export interface FullConfig {
    host: string;
    port: number;
    ssl: boolean;
    timeout: number;
}

// ts_ext_garbage_marker_005
const GARBAGE_CONFIG = { garbage: true };
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
        must_include=["updater.ts"],
        must_not_include=["ts_ext_garbage_marker_005"],
        commit_message="Add Partial usage",
    ),
    DiffTestCase(
        name="ts_ext_006_required_type",
        initial_files={
            "options.ts": """export interface Options {
    name?: string;
    value?: number;
    enabled?: boolean;
}

// ts_ext_garbage_marker_006
const GARBAGE_OPTIONS = { garbage: undefined };
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
        must_include=["validator.ts"],
        must_not_include=["ts_ext_garbage_marker_006"],
        commit_message="Add Required usage",
    ),
    DiffTestCase(
        name="ts_ext_007_pick_type",
        initial_files={
            "user.ts": """export interface User {
    id: string;
    name: string;
    email: string;
    password: string;
    createdAt: Date;
}

// ts_ext_garbage_marker_007
const GARBAGE_USER = { id: 'garbage' };
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
        must_include=["dto.ts"],
        must_not_include=["ts_ext_garbage_marker_007"],
        commit_message="Add Pick usage",
    ),
    DiffTestCase(
        name="ts_ext_008_omit_type",
        initial_files={
            "full.ts": """export interface FullRecord {
    id: string;
    name: string;
    secret: string;
    internal: boolean;
}

// ts_ext_garbage_marker_008
interface GarbageRecord { garbage: string }
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
        must_include=["public.ts"],
        must_not_include=["ts_ext_garbage_marker_008"],
        commit_message="Add Omit usage",
    ),
    DiffTestCase(
        name="ts_ext_009_return_type",
        initial_files={
            "factory.ts": """export function createUser(name: string, age: number) {
    return { id: Date.now().toString(), name, age, createdAt: new Date() };
}

// ts_ext_garbage_marker_009
function garbageFactory() { return { garbage: true }; }
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
        must_include=["types.ts"],
        must_not_include=["ts_ext_garbage_marker_009"],
        commit_message="Add ReturnType usage",
    ),
    DiffTestCase(
        name="ts_ext_010_parameters_type",
        initial_files={
            "api.ts": """export function fetchData(url: string, options: { method: string; headers: Record<string, string> }) {
    return fetch(url, options);
}

// ts_ext_garbage_marker_010
function garbageApi() { return null; }
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
        must_include=["wrapper.ts"],
        must_not_include=["ts_ext_garbage_marker_010"],
        commit_message="Add Parameters usage",
    ),
]

REACT_ADVANCED_CASES = [
    DiffTestCase(
        name="react_adv_001_component_with_props",
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

// react_adv_garbage_marker_001
const GARBAGE_CARD_CONFIG = { maxWidth: 300 };
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
        must_include=["App.tsx"],
        must_not_include=["react_adv_garbage_marker_001"],
        commit_message="Add Card usage",
    ),
    DiffTestCase(
        name="react_adv_002_usestate_generic",
        initial_files={
            "types.ts": """export interface TodoItem {
    id: string;
    text: string;
    completed: boolean;
}

// react_adv_garbage_marker_002
interface GarbageTodo { garbage: boolean }
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
        must_include=["TodoList.tsx"],
        must_not_include=["react_adv_garbage_marker_002"],
        commit_message="Add useState with TodoItem type",
    ),
    DiffTestCase(
        name="react_adv_003_usecontext",
        initial_files={
            "ThemeContext.tsx": """import { createContext } from 'react';

export interface Theme {
    primary: string;
    secondary: string;
}

export const ThemeContext = createContext<Theme>({ primary: '#000', secondary: '#fff' });

// react_adv_garbage_marker_003
const GARBAGE_THEME = { garbage: '#000' };
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
        must_include=["Button.tsx"],
        must_not_include=["react_adv_garbage_marker_003"],
        commit_message="Add ThemeContext usage",
    ),
    DiffTestCase(
        name="react_adv_004_usereducer",
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

// react_adv_garbage_marker_004
const GARBAGE_STATE = { garbage: 0 };
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
        must_include=["Counter.tsx"],
        must_not_include=["react_adv_garbage_marker_004"],
        commit_message="Add useReducer",
    ),
    DiffTestCase(
        name="react_adv_005_usememo",
        initial_files={
            "compute.ts": """export function expensiveComputation(items: number[]): number {
    return items.reduce((sum, n) => sum + n * n, 0);
}

// react_adv_garbage_marker_005
function garbageComputation() { return 0; }
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
        must_include=["Stats.tsx"],
        must_not_include=["react_adv_garbage_marker_005"],
        commit_message="Add useMemo",
    ),
    DiffTestCase(
        name="react_adv_006_custom_hook",
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

// react_adv_garbage_marker_006
const GARBAGE_API_CONFIG = { timeout: 9999 };
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
        must_include=["UserList.tsx"],
        must_not_include=["react_adv_garbage_marker_006"],
        commit_message="Add useApi hook usage",
    ),
    DiffTestCase(
        name="react_adv_007_forward_ref",
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

// react_adv_garbage_marker_007
const GARBAGE_INPUT_CONFIG = { maxLength: 100 };
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
        must_include=["Form.tsx"],
        must_not_include=["react_adv_garbage_marker_007"],
        commit_message="Add forwardRef usage",
    ),
    DiffTestCase(
        name="react_adv_008_react_memo",
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

// react_adv_garbage_marker_008
const GARBAGE_LIST_CONFIG = { maxItems: 100 };
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
        must_include=["Dashboard.tsx"],
        must_not_include=["react_adv_garbage_marker_008"],
        commit_message="Add memoized component usage",
    ),
    DiffTestCase(
        name="react_adv_009_use_callback",
        initial_files={
            "handlers.ts": """export function createClickHandler(id: string) {
    return () => console.log('Clicked:', id);
}

// react_adv_garbage_marker_009
function garbageHandler() { return null; }
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
        must_include=["ActionButton.tsx"],
        must_not_include=["react_adv_garbage_marker_009"],
        commit_message="Add useCallback",
    ),
    DiffTestCase(
        name="react_adv_010_redux_action",
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

// react_adv_garbage_marker_010
const GARBAGE_SLICE_CONFIG = { maxUsers: 100 };
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
        must_include=["UserForm.tsx"],
        must_not_include=["react_adv_garbage_marker_010"],
        commit_message="Add Redux action dispatch",
    ),
]

NODE_BACKEND_CASES = [
    DiffTestCase(
        name="node_001_express_middleware",
        initial_files={
            "authMiddleware.ts": """import { Request, Response, NextFunction } from 'express';

export function authMiddleware(req: Request, res: Response, next: NextFunction) {
    const token = req.headers.authorization;
    if (!token) {
        return res.status(401).json({ error: 'Unauthorized' });
    }
    next();
}

// node_garbage_marker_001
const GARBAGE_MIDDLEWARE_CONFIG = { skipPaths: [] };
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
        must_include=["app.ts"],
        must_not_include=["node_garbage_marker_001"],
        commit_message="Add middleware usage",
    ),
    DiffTestCase(
        name="node_002_route_handler",
        initial_files={
            "userHandler.ts": """import { Request, Response } from 'express';

export async function getUserHandler(req: Request, res: Response) {
    const { id } = req.params;
    res.json({ id, name: 'User' });
}

// node_garbage_marker_002
async function garbageHandler() { return null; }
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
        must_include=["routes.ts"],
        must_not_include=["node_garbage_marker_002"],
        commit_message="Add route handler",
    ),
    DiffTestCase(
        name="node_003_request_body_validation",
        initial_files={
            "schemas.ts": """export interface CreateUserBody {
    name: string;
    email: string;
    password: string;
}

// node_garbage_marker_003
interface GarbageBody { garbage: string }
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
        must_include=["controller.ts"],
        must_not_include=["node_garbage_marker_003"],
        commit_message="Add body validation",
    ),
    DiffTestCase(
        name="node_004_response_json",
        initial_files={
            "service.ts": """export interface ApiResponse<T> {
    data: T;
    success: boolean;
    timestamp: number;
}

export function createResponse<T>(data: T): ApiResponse<T> {
    return { data, success: true, timestamp: Date.now() };
}

// node_garbage_marker_004
const GARBAGE_RESPONSE = { garbage: true };
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
        must_include=["handler.ts"],
        must_not_include=["node_garbage_marker_004"],
        commit_message="Add response helper",
    ),
    DiffTestCase(
        name="node_005_socket_event",
        initial_files={
            "events.ts": """export interface ChatMessage {
    userId: string;
    text: string;
    timestamp: number;
}

export const CHAT_EVENT = 'chat:message';

// node_garbage_marker_005
const GARBAGE_EVENT = 'garbage:event';
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
        must_include=["socket.ts"],
        must_not_include=["node_garbage_marker_005"],
        commit_message="Add socket handler",
    ),
]

TEST_FRAMEWORK_CASES = [
    DiffTestCase(
        name="jest_001_describe_module",
        initial_files={
            "calculator.ts": """export function add(a: number, b: number): number {
    return a + b;
}

export function multiply(a: number, b: number): number {
    return a * b;
}

// jest_garbage_marker_001
function garbageCalculation() { return 0; }
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
        must_include=["calculator.test.ts"],
        must_not_include=["jest_garbage_marker_001"],
        commit_message="Add calculator tests",
    ),
    DiffTestCase(
        name="jest_002_it_calls_function",
        initial_files={
            "validator.ts": r"""export function isValidEmail(email: string): boolean {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// jest_garbage_marker_002
function garbageValidator() { return false; }
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
        must_include=["validator.test.ts"],
        must_not_include=["jest_garbage_marker_002"],
        commit_message="Add validator tests",
    ),
    DiffTestCase(
        name="jest_003_mock_module",
        initial_files={
            "api.ts": """export async function fetchUser(id: string) {
    const response = await fetch(`/api/users/${id}`);
    return response.json();
}

// jest_garbage_marker_003
async function garbageApi() { return null; }
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
        must_include=["service.test.ts"],
        must_not_include=["jest_garbage_marker_003"],
        commit_message="Add service tests with mock",
    ),
    DiffTestCase(
        name="jest_004_spy_on_method",
        initial_files={
            "logger.ts": """export const logger = {
    log: (message: string) => console.log(message),
    error: (message: string) => console.error(message),
};

// jest_garbage_marker_004
const garbageLogger = { garbage: () => null };
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
        must_include=["app.test.ts"],
        must_not_include=["jest_garbage_marker_004"],
        commit_message="Add app tests with spy",
    ),
    DiffTestCase(
        name="vitest_001_vi_fn",
        initial_files={
            "callback.ts": """export type Callback = (value: number) => void;

export function processNumbers(numbers: number[], callback: Callback) {
    numbers.forEach(n => callback(n));
}

// vitest_garbage_marker_001
const garbageCallback = () => {};
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
        must_include=["callback.test.ts"],
        must_not_include=["vitest_garbage_marker_001"],
        commit_message="Add vitest tests",
    ),
    DiffTestCase(
        name="testing_library_001_render",
        initial_files={
            "Greeting.tsx": """interface GreetingProps {
    name: string;
}

export function Greeting({ name }: GreetingProps) {
    return <h1>Hello, {name}!</h1>;
}

// testing_library_garbage_marker_001
const GARBAGE_GREETING_CONFIG = { maxLength: 100 };
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
        must_include=["Greeting.test.tsx"],
        must_not_include=["testing_library_garbage_marker_001"],
        commit_message="Add Greeting tests",
    ),
    DiffTestCase(
        name="playwright_001_page_click",
        initial_files={
            "login.ts": """export function getLoginUrl(): string {
    return '/login';
}

export function getCredentials() {
    return { username: 'test', password: 'test123' };  // pragma: allowlist secret
}

// playwright_garbage_marker_001
const GARBAGE_LOGIN_CONFIG = { timeout: 5000 };
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
        must_include=["login.spec.ts"],
        must_not_include=["playwright_garbage_marker_001"],
        commit_message="Add login e2e test",
    ),
    DiffTestCase(
        name="cypress_001_cy_get",
        initial_files={
            "form.ts": """export const FORM_SELECTORS = {
    nameInput: '[data-testid=name-input]',
    emailInput: '[data-testid=email-input]',
    submitButton: '[data-testid=submit-btn]',
};

// cypress_garbage_marker_001
const GARBAGE_FORM_SELECTORS = { garbage: '[data-testid=garbage]' };
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
        must_include=["form.cy.ts"],
        must_not_include=["cypress_garbage_marker_001"],
        commit_message="Add cypress form test",
    ),
    DiffTestCase(
        name="storybook_001_story",
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

// storybook_garbage_marker_001
const GARBAGE_BUTTON_CONFIG = { maxWidth: 200 };
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
        must_include=["Button.stories.tsx"],
        must_not_include=["storybook_garbage_marker_001"],
        commit_message="Add Button storybook",
    ),
]

ALL_JS_EXTENDED_CASES = (
    JS_REVERSE_DEPENDENCY_CASES + TS_TYPE_CASES + REACT_ADVANCED_CASES + NODE_BACKEND_CASES + TEST_FRAMEWORK_CASES
)


@pytest.mark.parametrize("case", ALL_JS_EXTENDED_CASES, ids=lambda c: c.name)
def test_js_extended_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
