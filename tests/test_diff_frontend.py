import pytest

from tests.utils import DiffTestCase, DiffTestRunner

REACT_TEST_CASES = [
    DiffTestCase(
        name="react_001_component_props",
        initial_files={
            "types.ts": """export interface UserCardProps {
    user: User;
    onClick?: () => void;
    className?: string;
}

export interface User {
    id: string;
    name: string;
    email: string;
    avatar?: string;
}

// react_garbage_marker_001
function unusedGarbageFunction() {
    return "this should not appear in context";
}
""",
            "App.tsx": """import React from 'react';

export function App() {
    return <div>Initial</div>;
}
""",
        },
        changed_files={
            "UserCard.tsx": """import React from 'react';
import { UserCardProps } from './types';

export function UserCard({ user, onClick, className }: UserCardProps) {
    return (
        <div className={className} onClick={onClick}>
            <img src={user.avatar} alt={user.name} />
            <h2>{user.name}</h2>
            <p>{user.email}</p>
        </div>
    );
}
""",
            "App.tsx": """import React from 'react';
import { UserCard } from './UserCard';
import { User } from './types';

const currentUser: User = {
    id: '1',
    name: 'John Doe',
    email: 'john@example.com',
};

export function App() {
    return <UserCard user={currentUser} />;
}
""",
        },
        must_include=["UserCard"],
        must_not_include=["react_garbage_marker_001"],
        commit_message="Add UserCard component with props",
    ),
    DiffTestCase(
        name="react_002_usestate_hook",
        initial_files={
            "types.ts": """export interface User {
    id: string;
    name: string;
    email: string;
}

export interface Post {
    id: string;
    title: string;
    content: string;
    authorId: string;
}

// react_garbage_marker_002
const GARBAGE_CONSTANT = "should not appear";
""",
            "UserList.tsx": """import React from 'react';

export function UserList() {
    return <div>Initial</div>;
}
""",
        },
        changed_files={
            "UserList.tsx": """import React, { useState } from 'react';
import { User } from './types';

export function UserList() {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(false);

    const addUser = (user: User) => {
        setUsers(prev => [...prev, user]);
    };

    return (
        <div>
            {loading ? <p>Loading...</p> : null}
            {users.map(user => (
                <div key={user.id}>{user.name}</div>
            ))}
        </div>
    );
}
""",
        },
        must_include=["UserList.tsx", "useState"],
        must_not_include=["react_garbage_marker_002"],
        commit_message="Add useState with User type",
    ),
    DiffTestCase(
        name="react_003_useeffect_dependency",
        initial_files={
            "api.ts": r"""export async function fetchData(endpoint: string): Promise<any> {
    const response = await fetch(\`/api/\${endpoint}\`);
    return response.json();
}

export async function fetchUsers(): Promise<any[]> {
    return fetchData('users');
}

// react_garbage_marker_003
function garbageHelperFunction() {
    return null;
}
""",
            "Dashboard.tsx": """import React from 'react';

export function Dashboard() {
    return <div>Initial</div>;
}
""",
        },
        changed_files={
            "Dashboard.tsx": """import React, { useEffect, useState } from 'react';
import { fetchData } from './api';

export function Dashboard() {
    const [data, setData] = useState(null);

    useEffect(() => {
        fetchData('dashboard').then(setData);
    }, []);

    return (
        <div>
            {data ? <pre>{JSON.stringify(data)}</pre> : <p>Loading...</p>}
        </div>
    );
}
""",
        },
        must_include=["Dashboard.tsx", "useEffect"],
        must_not_include=["react_garbage_marker_003"],
        commit_message="Add useEffect with fetchData dependency",
    ),
    DiffTestCase(
        name="react_004_usecontext",
        initial_files={
            "ThemeContext.tsx": """import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface Theme {
    primary: string;
    secondary: string;
    background: string;
}

export interface ThemeContextValue {
    theme: Theme;
    toggleTheme: () => void;
}

export const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
    const [isDark, setIsDark] = useState(false);

    const theme: Theme = isDark
        ? { primary: '#fff', secondary: '#ccc', background: '#222' }
        : { primary: '#000', secondary: '#333', background: '#fff' };

    const toggleTheme = () => setIsDark(prev => !prev);

    return (
        <ThemeContext.Provider value={{ theme, toggleTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}

// react_garbage_marker_004
const UNUSED_THEME_CONFIG = { unused: true };
""",
            "ThemedButton.tsx": """import React from 'react';

export function ThemedButton() {
    return <button>Initial</button>;
}
""",
        },
        changed_files={
            "ThemedButton.tsx": """import React, { useContext } from 'react';
import { ThemeContext } from './ThemeContext';

export function ThemedButton({ label }: { label: string }) {
    const themeContext = useContext(ThemeContext);

    if (!themeContext) {
        return <button>{label}</button>;
    }

    const { theme, toggleTheme } = themeContext;

    return (
        <button
            style={{ color: theme.primary, background: theme.background }}
            onClick={toggleTheme}
        >
            {label}
        </button>
    );
}
""",
        },
        must_include=["ThemedButton.tsx", "useContext"],
        must_not_include=["react_garbage_marker_004"],
        commit_message="Add useContext for ThemeContext",
    ),
    DiffTestCase(
        name="react_005_usereducer",
        initial_files={
            "counterReducer.ts": """export interface CounterState {
    count: number;
    step: number;
}

export type CounterAction =
    | { type: 'INCREMENT' }
    | { type: 'DECREMENT' }
    | { type: 'SET_STEP'; payload: number }
    | { type: 'RESET' };

export const initialState: CounterState = {
    count: 0,
    step: 1,
};

export function counterReducer(state: CounterState, action: CounterAction): CounterState {
    switch (action.type) {
        case 'INCREMENT':
            return { ...state, count: state.count + state.step };
        case 'DECREMENT':
            return { ...state, count: state.count - state.step };
        case 'SET_STEP':
            return { ...state, step: action.payload };
        case 'RESET':
            return initialState;
        default:
            return state;
    }
}

// react_garbage_marker_005
function unusedReducerHelper() { return null; }
""",
            "Counter.tsx": """import React from 'react';

export function Counter() {
    return <div>Initial</div>;
}
""",
        },
        changed_files={
            "Counter.tsx": """import React, { useReducer } from 'react';
import { counterReducer, initialState } from './counterReducer';

export function Counter() {
    const [state, dispatch] = useReducer(counterReducer, initialState);

    return (
        <div>
            <p>Count: {state.count}</p>
            <p>Step: {state.step}</p>
            <button onClick={() => dispatch({ type: 'INCREMENT' })}>+</button>
            <button onClick={() => dispatch({ type: 'DECREMENT' })}>-</button>
            <button onClick={() => dispatch({ type: 'RESET' })}>Reset</button>
        </div>
    );
}
""",
        },
        must_include=["Counter.tsx", "useReducer"],
        must_not_include=["react_garbage_marker_005"],
        commit_message="Add useReducer with counterReducer",
    ),
    DiffTestCase(
        name="react_006_custom_hook",
        initial_files={
            "useApi.ts": """import { useState, useEffect } from 'react';

export interface UseApiResult<T> {
    data: T | null;
    loading: boolean;
    error: Error | null;
    refetch: () => void;
}

export function useApi<T>(endpoint: string): UseApiResult<T> {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    const fetchData = async () => {
        setLoading(true);
        try {
            const response = await fetch(endpoint);
            const result = await response.json();
            setData(result);
            setError(null);
        } catch (e) {
            setError(e as Error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [endpoint]);

    return { data, loading, error, refetch: fetchData };
}

// react_garbage_marker_006
const GARBAGE_API_CONFIG = { timeout: 9999 };
""",
            "UserProfile.tsx": """import React from 'react';

export function UserProfile() {
    return <div>Initial</div>;
}
""",
        },
        changed_files={
            "UserProfile.tsx": r"""import React from 'react';
import { useApi } from './useApi';

interface User {
    id: string;
    name: string;
    email: string;
}

export function UserProfile({ userId }: { userId: string }) {
    const { data: user, loading, error, refetch } = useApi<User>(\`/users/\${userId}\`);

    if (loading) return <p>Loading...</p>;
    if (error) return <p>Error: {error.message}</p>;
    if (!user) return <p>User not found</p>;

    return (
        <div>
            <h1>{user.name}</h1>
            <p>{user.email}</p>
            <button onClick={refetch}>Refresh</button>
        </div>
    );
}
""",
        },
        must_include=["UserProfile.tsx", "useApi"],
        must_not_include=["react_garbage_marker_006"],
        commit_message="Add custom useApi hook usage",
    ),
    DiffTestCase(
        name="react_007_forwardref",
        initial_files={
            "InputField.tsx": """import React from 'react';

export function InputField() {
    return <input />;
}

// react_garbage_marker_007
const UNUSED_INPUT_CONFIG = { maxLength: 100 };
""",
            "Form.tsx": """import React from 'react';

export function Form() {
    return <form>Initial</form>;
}
""",
        },
        changed_files={
            "InputField.tsx": """import React, { forwardRef, InputHTMLAttributes } from 'react';

export interface InputFieldProps extends InputHTMLAttributes<HTMLInputElement> {
    label: string;
    error?: string;
}

export const InputField = forwardRef<HTMLInputElement, InputFieldProps>(
    ({ label, error, ...props }, ref) => {
        return (
            <div>
                <label>{label}</label>
                <input ref={ref} {...props} />
                {error && <span className="error">{error}</span>}
            </div>
        );
    }
);

InputField.displayName = 'InputField';
""",
            "Form.tsx": """import React, { useRef } from 'react';
import { InputField } from './InputField';

export function Form() {
    const nameRef = useRef<HTMLInputElement>(null);
    const emailRef = useRef<HTMLInputElement>(null);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        nameRef.current?.focus();
    };

    return (
        <form onSubmit={handleSubmit}>
            <InputField ref={nameRef} label="Name" name="name" />
            <InputField ref={emailRef} label="Email" name="email" type="email" />
            <button type="submit">Submit</button>
        </form>
    );
}
""",
        },
        must_include=["forwardRef"],
        must_not_include=["react_garbage_marker_007"],
        commit_message="Add forwardRef to InputField",
    ),
    DiffTestCase(
        name="react_008_memo",
        initial_files={
            "ExpensiveComponent.tsx": """import React from 'react';

export function ExpensiveComponent() {
    return <div>Initial</div>;
}

// react_garbage_marker_008
const GARBAGE_MEMO_DATA = ["unused", "data"];
""",
            "ParentComponent.tsx": """import React from 'react';

export function ParentComponent() {
    return <div>Initial</div>;
}
""",
        },
        changed_files={
            "ExpensiveComponent.tsx": """import React, { memo } from 'react';

interface ExpensiveComponentProps {
    items: string[];
    onItemClick: (item: string) => void;
}

function areEqual(
    prevProps: ExpensiveComponentProps,
    nextProps: ExpensiveComponentProps
): boolean {
    return prevProps.items.length === nextProps.items.length &&
           prevProps.items.every((item, i) => item === nextProps.items[i]);
}

export const ExpensiveComponent = memo(function ExpensiveComponent({
    items,
    onItemClick,
}: ExpensiveComponentProps) {
    console.log('ExpensiveComponent rendering');

    return (
        <ul>
            {items.map((item, index) => (
                <li key={index} onClick={() => onItemClick(item)}>
                    {item}
                </li>
            ))}
        </ul>
    );
}, areEqual);
""",
            "ParentComponent.tsx": """import React, { useState, useCallback } from 'react';
import { ExpensiveComponent } from './ExpensiveComponent';

export function ParentComponent() {
    const [items] = useState(['apple', 'banana', 'cherry']);
    const [count, setCount] = useState(0);

    const handleItemClick = useCallback((item: string) => {
        console.log('Clicked:', item);
    }, []);

    return (
        <div>
            <p>Count: {count}</p>
            <button onClick={() => setCount(c => c + 1)}>Increment</button>
            <ExpensiveComponent items={items} onItemClick={handleItemClick} />
        </div>
    );
}
""",
        },
        must_include=["memo"],
        must_not_include=["react_garbage_marker_008"],
        commit_message="Add React.memo with custom comparison",
    ),
    DiffTestCase(
        name="react_009_usememo_usecallback",
        initial_files={
            "utils.ts": """export function expensiveCalculation(items: number[]): number {
    console.log('Running expensive calculation');
    return items.reduce((acc, item) => acc + item * item, 0);
}

export function formatNumber(num: number): string {
    return new Intl.NumberFormat('en-US').format(num);
}

// react_garbage_marker_009
function garbageUtilFunction() { return 42; }
""",
            "DataDisplay.tsx": """import React from 'react';

export function DataDisplay() {
    return <div>Initial</div>;
}
""",
        },
        changed_files={
            "DataDisplay.tsx": """import React, { useMemo, useCallback, useState } from 'react';
import { expensiveCalculation, formatNumber } from './utils';

interface DataDisplayProps {
    items: number[];
}

export function DataDisplay({ items }: DataDisplayProps) {
    const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

    const total = useMemo(() => {
        return expensiveCalculation(items);
    }, [items]);

    const formattedTotal = useMemo(() => {
        return formatNumber(total);
    }, [total]);

    const handleSelect = useCallback((index: number) => {
        setSelectedIndex(index);
    }, []);

    const handleReset = useCallback(() => {
        setSelectedIndex(null);
    }, []);

    return (
        <div>
            <p>Total: {formattedTotal}</p>
            <ul>
                {items.map((item, index) => (
                    <li
                        key={index}
                        onClick={() => handleSelect(index)}
                        style={{ fontWeight: selectedIndex === index ? 'bold' : 'normal' }}
                    >
                        {item}
                    </li>
                ))}
            </ul>
            <button onClick={handleReset}>Reset</button>
        </div>
    );
}
""",
        },
        must_include=["DataDisplay.tsx", "useMemo", "useCallback"],
        must_not_include=["react_garbage_marker_009"],
        commit_message="Add useMemo and useCallback",
    ),
]

REDUX_TEST_CASES = [
    DiffTestCase(
        name="redux_001_action",
        initial_files={
            "userSlice.ts": """import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface User {
    id: string;
    name: string;
    email: string;
}

export interface UserState {
    users: User[];
    currentUser: User | null;
    loading: boolean;
}

const initialState: UserState = {
    users: [],
    currentUser: null,
    loading: false,
};

export const userSlice = createSlice({
    name: 'user',
    initialState,
    reducers: {
        setUsers: (state, action: PayloadAction<User[]>) => {
            state.users = action.payload;
        },
        updateUser: (state, action: PayloadAction<User>) => {
            const index = state.users.findIndex(u => u.id === action.payload.id);
            if (index !== -1) {
                state.users[index] = action.payload;
            }
            if (state.currentUser?.id === action.payload.id) {
                state.currentUser = action.payload;
            }
        },
        setCurrentUser: (state, action: PayloadAction<User | null>) => {
            state.currentUser = action.payload;
        },
        setLoading: (state, action: PayloadAction<boolean>) => {
            state.loading = action.payload;
        },
    },
});

export const { setUsers, updateUser, setCurrentUser, setLoading } = userSlice.actions;
export default userSlice.reducer;

// redux_garbage_marker_001
const GARBAGE_SLICE_CONFIG = { unused: true };
""",
            "UserEditor.tsx": """import React from 'react';

export function UserEditor() {
    return <div>Initial</div>;
}
""",
        },
        changed_files={
            "UserEditor.tsx": """import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { updateUser, User } from './userSlice';
import type { RootState } from './store';

export function UserEditor() {
    const dispatch = useDispatch();
    const currentUser = useSelector((state: RootState) => state.user.currentUser);
    const [name, setName] = useState(currentUser?.name || '');
    const [email, setEmail] = useState(currentUser?.email || '');

    const handleSave = () => {
        if (currentUser) {
            dispatch(updateUser({
                ...currentUser,
                name,
                email,
            }));
        }
    };

    if (!currentUser) {
        return <p>No user selected</p>;
    }

    return (
        <div>
            <input value={name} onChange={e => setName(e.target.value)} />
            <input value={email} onChange={e => setEmail(e.target.value)} />
            <button onClick={handleSave}>Save</button>
        </div>
    );
}
""",
        },
        must_include=["UserEditor.tsx", "dispatch", "useSelector"],
        must_not_include=["redux_garbage_marker_001"],
        commit_message="Add Redux dispatch with updateUser action",
    ),
    DiffTestCase(
        name="redux_002_selector",
        initial_files={
            "selectors.ts": """import { createSelector } from '@reduxjs/toolkit';
import type { RootState } from './store';

export const selectUsers = (state: RootState) => state.user.users;
export const selectLoading = (state: RootState) => state.user.loading;

export const selectActiveUsers = createSelector(
    [selectUsers],
    (users) => users.filter(user => user.email.includes('@'))
);

export const selectUserCount = createSelector(
    [selectUsers],
    (users) => users.length
);

export const selectActiveUserCount = createSelector(
    [selectActiveUsers],
    (activeUsers) => activeUsers.length
);

// redux_garbage_marker_002
const GARBAGE_SELECTOR_CONFIG = { cache: false };
""",
            "store.ts": """import { configureStore } from '@reduxjs/toolkit';
import userReducer from './userSlice';

export const store = configureStore({
    reducer: {
        user: userReducer,
    },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
""",
            "UserStats.tsx": """import React from 'react';

export function UserStats() {
    return <div>Initial</div>;
}
""",
        },
        changed_files={
            "UserStats.tsx": """import React from 'react';
import { useSelector } from 'react-redux';
import { selectActiveUsers, selectUserCount, selectActiveUserCount } from './selectors';

export function UserStats() {
    const activeUsers = useSelector(selectActiveUsers);
    const totalCount = useSelector(selectUserCount);
    const activeCount = useSelector(selectActiveUserCount);

    return (
        <div>
            <h2>User Statistics</h2>
            <p>Total users: {totalCount}</p>
            <p>Active users: {activeCount}</p>
            <ul>
                {activeUsers.map(user => (
                    <li key={user.id}>{user.name}</li>
                ))}
            </ul>
        </div>
    );
}
""",
        },
        must_include=["UserStats.tsx", "selectActiveUsers"],
        must_not_include=["redux_garbage_marker_002"],
        commit_message="Add Redux selectors usage",
    ),
]

VUE_TEST_CASES = [
    DiffTestCase(
        name="vue_001_reactive",
        initial_files={
            "Counter.vue": """<template>
    <div>Initial</div>
</template>

<script setup lang="ts">
// vue_garbage_marker_001
const GARBAGE_CONFIG = { unused: true };
</script>
""",
        },
        changed_files={
            "Counter.vue": """<template>
    <div class="counter">
        <p>Count: {{ count }}</p>
        <p>Double: {{ doubleCount }}</p>
        <button @click="increment">+</button>
        <button @click="decrement">-</button>
        <button @click="reset">Reset</button>
    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const count = ref(0);

const doubleCount = computed(() => count.value * 2);

function increment() {
    count.value++;
}

function decrement() {
    count.value--;
}

function reset() {
    count.value = 0;
}
</script>
""",
        },
        must_include=["Counter.vue", "ref", "computed"],
        must_not_include=["vue_garbage_marker_001"],
        commit_message="Add Vue ref reactivity",
    ),
    DiffTestCase(
        name="vue_002_computed",
        initial_files={
            "utils.ts": """export function formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    }).format(price);
}

export function calculateDiscount(price: number, discount: number): number {
    return price * (1 - discount / 100);
}

// vue_garbage_marker_002
function garbageUtilFunction() { return 0; }
""",
            "PriceCalculator.vue": """<template>
    <div>Initial</div>
</template>

<script setup lang="ts">
</script>
""",
        },
        changed_files={
            "PriceCalculator.vue": """<template>
    <div class="price-calculator">
        <input v-model.number="basePrice" type="number" placeholder="Price" />
        <input v-model.number="discountPercent" type="number" placeholder="Discount %" />
        <p>Original: {{ formattedPrice }}</p>
        <p>Discounted: {{ formattedDiscountedPrice }}</p>
        <p>Savings: {{ formattedSavings }}</p>
    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { formatPrice, calculateDiscount } from './utils';

const basePrice = ref(100);
const discountPercent = ref(10);

const discountedPrice = computed(() => {
    return calculateDiscount(basePrice.value, discountPercent.value);
});

const savings = computed(() => {
    return basePrice.value - discountedPrice.value;
});

const formattedPrice = computed(() => formatPrice(basePrice.value));
const formattedDiscountedPrice = computed(() => formatPrice(discountedPrice.value));
const formattedSavings = computed(() => formatPrice(savings.value));
</script>
""",
        },
        must_include=["PriceCalculator.vue", "computed"],
        must_not_include=["vue_garbage_marker_002"],
        commit_message="Add Vue computed properties",
    ),
    DiffTestCase(
        name="vue_003_watch",
        initial_files={
            "api.ts": r"""export async function searchUsers(query: string): Promise<any[]> {
    const response = await fetch(\`/api/users?search=\${encodeURIComponent(query)}\`);
    return response.json();
}

export async function fetchUserDetails(userId: string): Promise<any> {
    const response = await fetch(\`/api/users/\${userId}\`);
    return response.json();
}

// vue_garbage_marker_003
const GARBAGE_API_TIMEOUT = 5000;
""",
            "UserSearch.vue": """<template>
    <div>Initial</div>
</template>

<script setup lang="ts">
</script>
""",
        },
        changed_files={
            "UserSearch.vue": """<template>
    <div class="user-search">
        <input v-model="searchQuery" placeholder="Search users..." />
        <p v-if="loading">Searching...</p>
        <ul v-else>
            <li v-for="user in results" :key="user.id">
                {{ user.name }}
            </li>
        </ul>
    </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { searchUsers } from './api';

const searchQuery = ref('');
const results = ref<any[]>([]);
const loading = ref(false);

watch(searchQuery, async (newQuery, oldQuery) => {
    if (newQuery.length < 2) {
        results.value = [];
        return;
    }

    loading.value = true;
    try {
        results.value = await searchUsers(newQuery);
    } finally {
        loading.value = false;
    }
}, { immediate: false });
</script>
""",
        },
        must_include=["UserSearch.vue", "watch"],
        must_not_include=["vue_garbage_marker_003"],
        commit_message="Add Vue watch for search",
    ),
    DiffTestCase(
        name="vue_004_defineprops",
        initial_files={
            "types.ts": """export interface CardProps {
    title: string;
    description?: string;
    imageUrl?: string;
    tags?: string[];
}

export interface CardAction {
    label: string;
    handler: () => void;
}

// vue_garbage_marker_004
const GARBAGE_CARD_CONFIG = { maxTags: 10 };
""",
            "Card.vue": """<template>
    <div>Initial</div>
</template>

<script setup lang="ts">
</script>
""",
        },
        changed_files={
            "Card.vue": """<template>
    <div class="card">
        <img v-if="imageUrl" :src="imageUrl" :alt="title" />
        <h3>{{ title }}</h3>
        <p v-if="description">{{ description }}</p>
        <div v-if="tags?.length" class="tags">
            <span v-for="tag in tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { CardProps } from './types';

const props = defineProps<CardProps>();

const hasImage = computed(() => !!props.imageUrl);
const tagCount = computed(() => props.tags?.length ?? 0);
</script>
""",
            "CardGrid.vue": """<template>
    <div class="card-grid">
        <Card
            v-for="item in items"
            :key="item.id"
            :title="item.title"
            :description="item.description"
            :imageUrl="item.imageUrl"
            :tags="item.tags"
        />
    </div>
</template>

<script setup lang="ts">
import Card from './Card.vue';
import type { CardProps } from './types';

interface CardItem extends CardProps {
    id: string;
}

defineProps<{
    items: CardItem[];
}>();
</script>
""",
        },
        must_include=["defineProps"],
        must_not_include=["vue_garbage_marker_004"],
        commit_message="Add Vue defineProps",
    ),
    DiffTestCase(
        name="vue_005_defineemits",
        initial_files={
            "Modal.vue": """<template>
    <div>Initial</div>
</template>

<script setup lang="ts">
// vue_garbage_marker_005
const GARBAGE_MODAL_CONFIG = { closeOnEscape: true };
</script>
""",
            "App.vue": """<template>
    <div>Initial</div>
</template>

<script setup lang="ts">
</script>
""",
        },
        changed_files={
            "Modal.vue": """<template>
    <div v-if="isOpen" class="modal-overlay" @click.self="handleClose">
        <div class="modal-content">
            <header>
                <h2>{{ title }}</h2>
                <button @click="handleClose">&times;</button>
            </header>
            <main>
                <slot></slot>
            </main>
            <footer>
                <button @click="handleCancel">Cancel</button>
                <button @click="handleConfirm">Confirm</button>
            </footer>
        </div>
    </div>
</template>

<script setup lang="ts">
defineProps<{
    isOpen: boolean;
    title: string;
}>();

const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'confirm'): void;
    (e: 'cancel'): void;
}>();

function handleClose() {
    emit('close');
}

function handleConfirm() {
    emit('confirm');
    emit('close');
}

function handleCancel() {
    emit('cancel');
    emit('close');
}
</script>
""",
            "App.vue": """<template>
    <div>
        <button @click="showModal = true">Open Modal</button>
        <Modal
            :isOpen="showModal"
            title="Confirm Action"
            @close="showModal = false"
            @confirm="handleConfirm"
            @cancel="handleCancel"
        >
            <p>Are you sure you want to proceed?</p>
        </Modal>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import Modal from './Modal.vue';

const showModal = ref(false);

function handleConfirm() {
    console.log('Confirmed!');
}

function handleCancel() {
    console.log('Cancelled');
}
</script>
""",
        },
        must_include=["defineEmits"],
        must_not_include=["vue_garbage_marker_005"],
        commit_message="Add Vue defineEmits",
    ),
]

ANGULAR_TEST_CASES = [
    DiffTestCase(
        name="angular_001_input",
        initial_files={
            "user.model.ts": """export interface User {
    id: string;
    name: string;
    email: string;
    avatar?: string;
    role: 'admin' | 'user' | 'guest';
}

export interface UserDisplayOptions {
    showAvatar: boolean;
    showRole: boolean;
    compact: boolean;
}

// angular_garbage_marker_001
const GARBAGE_USER_CONFIG = { maxUsers: 100 };
""",
            "user-card.component.ts": """import { Component } from '@angular/core';

@Component({
    selector: 'app-user-card',
    template: '<div>Initial</div>',
})
export class UserCardComponent {}
""",
        },
        changed_files={
            "user-card.component.ts": r"""import { Component, Input } from '@angular/core';
import { User, UserDisplayOptions } from './user.model';

@Component({
    selector: 'app-user-card',
    template: \`
        <div class="user-card" [class.compact]="options?.compact">
            <img *ngIf="options?.showAvatar && user?.avatar"
                 [src]="user.avatar"
                 [alt]="user.name" />
            <div class="info">
                <h3>{{ user?.name }}</h3>
                <p>{{ user?.email }}</p>
                <span *ngIf="options?.showRole" class="role">{{ user?.role }}</span>
            </div>
        </div>
    \`,
})
export class UserCardComponent {
    @Input() user: User | null = null;
    @Input() options: UserDisplayOptions = {
        showAvatar: true,
        showRole: true,
        compact: false,
    };
}
""",
            "user-list.component.ts": r"""import { Component } from '@angular/core';
import { User, UserDisplayOptions } from './user.model';

@Component({
    selector: 'app-user-list',
    template: \`
        <div class="user-list">
            <app-user-card
                *ngFor="let user of users"
                [user]="user"
                [options]="displayOptions">
            </app-user-card>
        </div>
    \`,
})
export class UserListComponent {
    users: User[] = [];
    displayOptions: UserDisplayOptions = {
        showAvatar: true,
        showRole: false,
        compact: true,
    };
}
""",
        },
        must_include=["@Input"],
        must_not_include=["angular_garbage_marker_001"],
        commit_message="Add Angular @Input decorator",
    ),
    DiffTestCase(
        name="angular_002_output",
        initial_files={
            "item-selector.component.ts": """import { Component } from '@angular/core';

@Component({
    selector: 'app-item-selector',
    template: '<div>Initial</div>',
})
export class ItemSelectorComponent {}

// angular_garbage_marker_002
const GARBAGE_SELECTOR_CONFIG = { multiSelect: false };
""",
            "parent.component.ts": """import { Component } from '@angular/core';

@Component({
    selector: 'app-parent',
    template: '<div>Initial</div>',
})
export class ParentComponent {}
""",
        },
        changed_files={
            "item-selector.component.ts": r"""import { Component, Input, Output, EventEmitter } from '@angular/core';

export interface Item {
    id: string;
    name: string;
    value: number;
}

export interface SelectionChangeEvent {
    selectedItems: Item[];
    lastSelected: Item | null;
}

@Component({
    selector: 'app-item-selector',
    template: \`
        <div class="item-selector">
            <div *ngFor="let item of items"
                 class="item"
                 [class.selected]="isSelected(item)"
                 (click)="toggleSelection(item)">
                {{ item.name }}
            </div>
            <button (click)="confirmSelection()">Confirm</button>
            <button (click)="cancelSelection()">Cancel</button>
        </div>
    \`,
})
export class ItemSelectorComponent {
    @Input() items: Item[] = [];
    @Input() multiSelect = false;

    @Output() selectionChange = new EventEmitter<SelectionChangeEvent>();
    @Output() confirm = new EventEmitter<Item[]>();
    @Output() cancel = new EventEmitter<void>();

    selectedItems: Item[] = [];

    isSelected(item: Item): boolean {
        return this.selectedItems.some(i => i.id === item.id);
    }

    toggleSelection(item: Item): void {
        if (this.isSelected(item)) {
            this.selectedItems = this.selectedItems.filter(i => i.id !== item.id);
        } else {
            if (this.multiSelect) {
                this.selectedItems = [...this.selectedItems, item];
            } else {
                this.selectedItems = [item];
            }
        }
        this.selectionChange.emit({
            selectedItems: this.selectedItems,
            lastSelected: item,
        });
    }

    confirmSelection(): void {
        this.confirm.emit(this.selectedItems);
    }

    cancelSelection(): void {
        this.selectedItems = [];
        this.cancel.emit();
    }
}
""",
            "parent.component.ts": r"""import { Component } from '@angular/core';
import { Item, SelectionChangeEvent } from './item-selector.component';

@Component({
    selector: 'app-parent',
    template: \`
        <app-item-selector
            [items]="items"
            [multiSelect]="true"
            (selectionChange)="onSelectionChange($event)"
            (confirm)="onConfirm($event)"
            (cancel)="onCancel()">
        </app-item-selector>
        <p>Selected: {{ selectedCount }}</p>
    \`,
})
export class ParentComponent {
    items: Item[] = [
        { id: '1', name: 'Item 1', value: 100 },
        { id: '2', name: 'Item 2', value: 200 },
        { id: '3', name: 'Item 3', value: 300 },
    ];
    selectedCount = 0;

    onSelectionChange(event: SelectionChangeEvent): void {
        this.selectedCount = event.selectedItems.length;
        console.log('Selection changed:', event);
    }

    onConfirm(items: Item[]): void {
        console.log('Confirmed:', items);
    }

    onCancel(): void {
        this.selectedCount = 0;
        console.log('Cancelled');
    }
}
""",
        },
        must_include=["@Output", "EventEmitter"],
        must_not_include=["angular_garbage_marker_002"],
        commit_message="Add Angular @Output decorator",
    ),
    DiffTestCase(
        name="angular_003_service_injection",
        initial_files={
            "auth.service.ts": """import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface AuthUser {
    id: string;
    email: string;
    token: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
    private currentUserSubject = new BehaviorSubject<AuthUser | null>(null);

    get currentUser$(): Observable<AuthUser | null> {
        return this.currentUserSubject.asObservable();
    }

    get isAuthenticated(): boolean {
        return this.currentUserSubject.value !== null;
    }

    login(email: string, password: string): Promise<AuthUser> {
        return fetch('/api/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        })
            .then(res => res.json())
            .then(user => {
                this.currentUserSubject.next(user);
                return user;
            });
    }

    logout(): void {
        this.currentUserSubject.next(null);
    }
}

// angular_garbage_marker_003
const GARBAGE_AUTH_CONFIG = { tokenExpiry: 3600 };
""",
            "user.service.ts": """import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class UserService {
    getUsers(): Promise<any[]> {
        return fetch('/api/users').then(res => res.json());
    }
}
""",
            "dashboard.component.ts": """import { Component } from '@angular/core';

@Component({
    selector: 'app-dashboard',
    template: '<div>Initial</div>',
})
export class DashboardComponent {}
""",
        },
        changed_files={
            "dashboard.component.ts": r"""import { Component, OnInit } from '@angular/core';
import { AuthService, AuthUser } from './auth.service';
import { UserService } from './user.service';

@Component({
    selector: 'app-dashboard',
    template: \`
        <div *ngIf="currentUser; else loginPrompt">
            <h1>Welcome, {{ currentUser.email }}</h1>
            <h2>Users</h2>
            <ul>
                <li *ngFor="let user of users">{{ user.name }}</li>
            </ul>
            <button (click)="logout()">Logout</button>
        </div>
        <ng-template #loginPrompt>
            <p>Please log in</p>
        </ng-template>
    \`,
})
export class DashboardComponent implements OnInit {
    currentUser: AuthUser | null = null;
    users: any[] = [];

    constructor(
        private authService: AuthService,
        private userService: UserService
    ) {}

    ngOnInit(): void {
        this.authService.currentUser$.subscribe(user => {
            this.currentUser = user;
            if (user) {
                this.loadUsers();
            }
        });
    }

    private async loadUsers(): Promise<void> {
        this.users = await this.userService.getUsers();
    }

    logout(): void {
        this.authService.logout();
    }
}
""",
        },
        must_include=["dashboard.component.ts", "AuthService", "UserService"],
        must_not_include=["angular_garbage_marker_003"],
        commit_message="Add Angular service injection",
    ),
    DiffTestCase(
        name="angular_004_httpclient",
        initial_files={
            "api.types.ts": """export interface ApiResponse<T> {
    data: T;
    message: string;
    status: number;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    pageSize: number;
}

export interface User {
    id: string;
    name: string;
    email: string;
}

export interface CreateUserRequest {
    name: string;
    email: string;
    password: string;
}

export interface UpdateUserRequest {
    name?: string;
    email?: string;
}

// angular_garbage_marker_004
const GARBAGE_API_CONFIG = { baseUrl: '/api' };
""",
            "api.service.ts": """import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ApiService {}
""",
        },
        changed_files={
            "api.service.ts": r"""import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { Observable, catchError, map } from 'rxjs';
import {
    ApiResponse,
    PaginatedResponse,
    User,
    CreateUserRequest,
    UpdateUserRequest,
} from './api.types';

@Injectable({ providedIn: 'root' })
export class ApiService {
    private baseUrl = '/api';

    constructor(private http: HttpClient) {}

    getUsers(page = 1, pageSize = 10): Observable<PaginatedResponse<User>> {
        const params = new HttpParams()
            .set('page', page.toString())
            .set('pageSize', pageSize.toString());

        return this.http
            .get<ApiResponse<PaginatedResponse<User>>>(\`\${this.baseUrl}/users\`, { params })
            .pipe(map(response => response.data));
    }

    getUser(id: string): Observable<User> {
        return this.http
            .get<ApiResponse<User>>(\`\${this.baseUrl}/users/\${id}\`)
            .pipe(map(response => response.data));
    }

    createUser(request: CreateUserRequest): Observable<User> {
        const headers = new HttpHeaders().set('Content-Type', 'application/json');

        return this.http
            .post<ApiResponse<User>>(\`\${this.baseUrl}/users\`, request, { headers })
            .pipe(map(response => response.data));
    }

    updateUser(id: string, request: UpdateUserRequest): Observable<User> {
        return this.http
            .patch<ApiResponse<User>>(\`\${this.baseUrl}/users/\${id}\`, request)
            .pipe(map(response => response.data));
    }

    deleteUser(id: string): Observable<void> {
        return this.http
            .delete<void>(\`\${this.baseUrl}/users/\${id}\`)
            .pipe(catchError(error => {
                console.error('Delete failed:', error);
                throw error;
            }));
    }
}
""",
            "user-management.component.ts": r"""import { Component, OnInit } from '@angular/core';
import { ApiService } from './api.service';
import { User, CreateUserRequest } from './api.types';

@Component({
    selector: 'app-user-management',
    template: \`
        <div class="user-management">
            <h1>User Management</h1>
            <button (click)="loadUsers()">Refresh</button>
            <ul>
                <li *ngFor="let user of users">
                    {{ user.name }} ({{ user.email }})
                    <button (click)="deleteUser(user.id)">Delete</button>
                </li>
            </ul>
            <form (ngSubmit)="createUser()">
                <input [(ngModel)]="newUser.name" placeholder="Name" name="name" />
                <input [(ngModel)]="newUser.email" placeholder="Email" name="email" />
                <input [(ngModel)]="newUser.password" type="password" placeholder="Password" name="password" />
                <button type="submit">Create</button>
            </form>
        </div>
    \`,
})
export class UserManagementComponent implements OnInit {
    users: User[] = [];
    newUser: CreateUserRequest = { name: '', email: '', password: '' };

    constructor(private apiService: ApiService) {}

    ngOnInit(): void {
        this.loadUsers();
    }

    loadUsers(): void {
        this.apiService.getUsers().subscribe(response => {
            this.users = response.items;
        });
    }

    createUser(): void {
        this.apiService.createUser(this.newUser).subscribe(user => {
            this.users.push(user);
            this.newUser = { name: '', email: '', password: '' };
        });
    }

    deleteUser(id: string): void {
        this.apiService.deleteUser(id).subscribe(() => {
            this.users = this.users.filter(u => u.id !== id);
        });
    }
}
""",
        },
        must_include=["HttpClient"],
        must_not_include=["angular_garbage_marker_004"],
        commit_message="Add Angular HttpClient usage",
    ),
]

TYPESCRIPT_TYPE_SYSTEM_CASES = [
    DiffTestCase(
        name="ts_001_interface_implementation",
        initial_files={
            "interfaces.ts": """export interface IService {
    start(): void;
    stop(): void;
    getStatus(): string;
}

export interface ILogger {
    log(message: string): void;
    error(message: string): void;
}

// ts_garbage_marker_001
const GARBAGE_INTERFACE_CONFIG = { version: 1 };
""",
            "service.ts": """console.log('initial');
""",
        },
        changed_files={
            "service.ts": """import { IService, ILogger } from './interfaces';

export class MyService implements IService {
    private running = false;
    private logger: ILogger;

    constructor(logger: ILogger) {
        this.logger = logger;
    }

    start(): void {
        this.running = true;
        this.logger.log('Service started');
    }

    stop(): void {
        this.running = false;
        this.logger.log('Service stopped');
    }

    getStatus(): string {
        return this.running ? 'running' : 'stopped';
    }
}
""",
        },
        must_include=["service.ts", "implements IService"],
        must_not_include=["ts_garbage_marker_001"],
        commit_message="Add service implementing IService",
    ),
    DiffTestCase(
        name="ts_002_type_extension",
        initial_files={
            "types.ts": """export type User = {
    id: string;
    name: string;
    email: string;
};

export type Timestamps = {
    createdAt: Date;
    updatedAt: Date;
};

// ts_garbage_marker_002
type GarbageType = { unused: boolean };
""",
            "extended.ts": """console.log('initial');
""",
        },
        changed_files={
            "extended.ts": """import { User, Timestamps } from './types';

export type ExtendedUser = User & {
    metadata: Record<string, unknown>;
    role: 'admin' | 'user';
};

export type TimestampedUser = User & Timestamps;

export type FullUser = User & Timestamps & {
    preferences: {
        theme: 'light' | 'dark';
        notifications: boolean;
    };
};
""",
        },
        must_include=["extended.ts", "ExtendedUser"],
        must_not_include=["ts_garbage_marker_002"],
        commit_message="Add extended user types",
    ),
    DiffTestCase(
        name="ts_003_generic_constraint",
        initial_files={
            "entities.ts": """export interface BaseEntity {
    id: string;
    createdAt: Date;
    updatedAt: Date;
}

export interface Identifiable {
    id: string;
}

export interface Timestamped {
    createdAt: Date;
    updatedAt: Date;
}

// ts_garbage_marker_003
interface GarbageEntity { garbage: true }
""",
            "repository.ts": """console.log('initial');
""",
        },
        changed_files={
            "repository.ts": """import { BaseEntity, Identifiable } from './entities';

export function findById<T extends BaseEntity>(
    items: T[],
    id: string
): T | undefined {
    return items.find(item => item.id === id);
}

export function updateEntity<T extends BaseEntity>(
    entity: T,
    updates: Partial<Omit<T, 'id' | 'createdAt'>>
): T {
    return {
        ...entity,
        ...updates,
        updatedAt: new Date(),
    };
}

export class Repository<T extends Identifiable> {
    private items: Map<string, T> = new Map();

    save(item: T): void {
        this.items.set(item.id, item);
    }

    get(id: string): T | undefined {
        return this.items.get(id);
    }
}
""",
        },
        must_include=["repository.ts", "extends BaseEntity"],
        must_not_include=["ts_garbage_marker_003"],
        commit_message="Add generic repository with constraints",
    ),
    DiffTestCase(
        name="ts_004_conditional_type",
        initial_files={
            "primitives.ts": """export type Primitive = string | number | boolean | null | undefined;

export type JsonValue = Primitive | JsonObject | JsonArray;
export interface JsonObject { [key: string]: JsonValue }
export interface JsonArray extends Array<JsonValue> {}

// ts_garbage_marker_004
type GarbagePrimitive = never;
""",
            "conditional.ts": """console.log('initial');
""",
        },
        changed_files={
            "conditional.ts": """import { Primitive } from './primitives';

export type Unwrap<T> = T extends Promise<infer U> ? U : T;

export type UnwrapArray<T> = T extends Array<infer U> ? U : T;

export type IsArray<T> = T extends unknown[] ? true : false;

export type IsPrimitive<T> = T extends Primitive ? true : false;

export type DeepUnwrap<T> = T extends Promise<infer U>
    ? DeepUnwrap<U>
    : T extends Array<infer V>
    ? Array<DeepUnwrap<V>>
    : T;

export type Flatten<T> = T extends Array<infer U>
    ? U extends Array<unknown>
        ? Flatten<U>
        : U
    : T;
""",
        },
        must_include=["conditional.ts", "Unwrap"],
        must_not_include=["ts_garbage_marker_004"],
        commit_message="Add conditional types",
    ),
    DiffTestCase(
        name="ts_005_mapped_type",
        initial_files={
            "models.ts": """export interface UserModel {
    id: string;
    name: string;
    email: string;
    password: string;
}

export interface ProductModel {
    id: string;
    name: string;
    price: number;
    stock: number;
}

// ts_garbage_marker_005
interface GarbageModel { garbage: string }
""",
            "mapped.ts": """console.log('initial');
""",
        },
        changed_files={
            "mapped.ts": """import { UserModel, ProductModel } from './models';

export type Readonly<T> = {
    readonly [K in keyof T]: T[K];
};

export type Mutable<T> = {
    -readonly [K in keyof T]: T[K];
};

export type Optional<T> = {
    [K in keyof T]?: T[K];
};

export type Required<T> = {
    [K in keyof T]-?: T[K];
};

export type Nullable<T> = {
    [K in keyof T]: T[K] | null;
};

export type ReadonlyUser = Readonly<UserModel>;
export type OptionalProduct = Optional<ProductModel>;
export type NullableUser = Nullable<UserModel>;
""",
        },
        must_include=["mapped.ts", "keyof T"],
        must_not_include=["ts_garbage_marker_005"],
        commit_message="Add mapped types",
    ),
    DiffTestCase(
        name="ts_006_template_literal_type",
        initial_files={
            "events.ts": """export type EventCategory = 'user' | 'system' | 'api';
export type EventAction = 'created' | 'updated' | 'deleted';

// ts_garbage_marker_006
type GarbageEvent = 'garbage';
""",
            "template_types.ts": """console.log('initial');
""",
        },
        changed_files={
            "template_types.ts": r"""import { EventCategory, EventAction } from './events';

export type EventName = \`\${EventCategory}:\${EventAction}\`;

export type Getters<T> = {
    [K in keyof T as \`get\${Capitalize<string & K>}\`]: () => T[K];
};

export type Setters<T> = {
    [K in keyof T as \`set\${Capitalize<string & K>}\`]: (value: T[K]) => void;
};

export type CSSProperty = \`\${'margin' | 'padding'}-\${'top' | 'right' | 'bottom' | 'left'}\`;

export type HTTPMethod = \`\${'GET' | 'POST' | 'PUT' | 'DELETE'}\`;

export type Endpoint = \`/\${string}\`;

export type Route = \`\${HTTPMethod} \${Endpoint}\`;

interface Person {
    name: string;
    age: number;
}

export type PersonGetters = Getters<Person>;
export type PersonSetters = Setters<Person>;
""",
        },
        must_include=["template_types.ts", "EventName"],
        must_not_include=["ts_garbage_marker_006"],
        commit_message="Add template literal types",
    ),
    DiffTestCase(
        name="ts_007_discriminated_union",
        initial_files={
            "results.ts": """export interface Success<T> {
    type: 'success';
    data: T;
    timestamp: Date;
}

export interface Failure {
    type: 'failure';
    error: Error;
    code: number;
}

export interface Loading {
    type: 'loading';
    progress?: number;
}

// ts_garbage_marker_007
interface GarbageResult { type: 'garbage' }
""",
            "handlers.ts": """console.log('initial');
""",
        },
        changed_files={
            "handlers.ts": r"""import { Success, Failure, Loading } from './results';

export type Result<T> = Success<T> | Failure | Loading;

export function handleResult<T>(result: Result<T>): string {
    switch (result.type) {
        case 'success':
            return \`Data received: \${JSON.stringify(result.data)}\`;
        case 'failure':
            return \`Error \${result.code}: \${result.error.message}\`;
        case 'loading':
            return \`Loading... \${result.progress ?? 0}%\`;
    }
}

export function isSuccess<T>(result: Result<T>): result is Success<T> {
    return result.type === 'success';
}

export function isFailure<T>(result: Result<T>): result is Failure {
    return result.type === 'failure';
}
""",
        },
        must_include=["handlers.ts", "Result<T>"],
        must_not_include=["ts_garbage_marker_007"],
        commit_message="Add discriminated union handlers",
    ),
    DiffTestCase(
        name="ts_008_type_guard",
        initial_files={
            "entities.ts": """export interface User {
    type: 'user';
    id: string;
    name: string;
    email: string;
}

export interface Admin extends User {
    type: 'admin';
    permissions: string[];
}

export interface Guest {
    type: 'guest';
    sessionId: string;
}

// ts_garbage_marker_008
interface GarbageEntity { type: 'garbage' }
""",
            "guards.ts": """console.log('initial');
""",
        },
        changed_files={
            "guards.ts": r"""import { User, Admin, Guest } from './entities';

export type Person = User | Admin | Guest;

export function isUser(obj: unknown): obj is User {
    return (
        typeof obj === 'object' &&
        obj !== null &&
        'type' in obj &&
        (obj as User).type === 'user'
    );
}

export function isAdmin(person: Person): person is Admin {
    return person.type === 'admin';
}

export function isGuest(person: Person): person is Guest {
    return person.type === 'guest';
}

export function hasEmail(person: Person): person is User | Admin {
    return 'email' in person;
}

export function processIdentity(person: Person): string {
    if (isAdmin(person)) {
        return \`Admin: \${person.name} with \${person.permissions.length} permissions\`;
    }
    if (isGuest(person)) {
        return \`Guest session: \${person.sessionId}\`;
    }
    return \`User: \${person.name}\`;
}
""",
        },
        must_include=["guards.ts", "person is Admin"],
        must_not_include=["ts_garbage_marker_008"],
        commit_message="Add type guards",
    ),
    DiffTestCase(
        name="ts_009_utility_types",
        initial_files={
            "models.ts": """export interface User {
    id: string;
    name: string;
    email: string;
    password: string;
    createdAt: Date;
    updatedAt: Date;
}

export interface Product {
    id: string;
    name: string;
    price: number;
    description: string;
    category: string;
    inStock: boolean;
}

// ts_garbage_marker_009
interface GarbageModel { garbage: true }
""",
            "dtos.ts": """console.log('initial');
""",
        },
        changed_files={
            "dtos.ts": """import { User, Product } from './models';

export type UserDTO = Omit<User, 'password'>;

export type CreateUserDTO = Pick<User, 'name' | 'email' | 'password'>;

export type UpdateUserDTO = Partial<Pick<User, 'name' | 'email'>>;

export type UserResponse = Readonly<UserDTO>;

export type ProductPreview = Pick<Product, 'id' | 'name' | 'price'>;

export type ProductUpdate = Partial<Omit<Product, 'id'>>;

export type RequiredProduct = Required<Partial<Product>>;

export type NonNullableUser = {
    [K in keyof User]: NonNullable<User[K]>;
};

export function toUserDTO(user: User): UserDTO {
    const { password, ...dto } = user;
    return dto;
}

export function createUser(data: CreateUserDTO): User {
    return {
        ...data,
        id: crypto.randomUUID(),
        createdAt: new Date(),
        updatedAt: new Date(),
    };
}
""",
        },
        must_include=["dtos.ts", "Omit<User"],
        must_not_include=["ts_garbage_marker_009"],
        commit_message="Add utility types usage",
    ),
    DiffTestCase(
        name="ts_010_infer_keyword",
        initial_files={
            "functions.ts": """export function createUser(name: string, age: number): { id: string; name: string; age: number } {
    return { id: crypto.randomUUID(), name, age };
}

export async function fetchData<T>(url: string): Promise<T> {
    const response = await fetch(url);
    return response.json();
}

export type EventHandler<T> = (event: T) => void;

// ts_garbage_marker_010
function garbageFunction() { return null; }
""",
            "infer_types.ts": """console.log('initial');
""",
        },
        changed_files={
            "infer_types.ts": """import { createUser, fetchData, EventHandler } from './functions';

export type ReturnTypeOf<T> = T extends (...args: any[]) => infer R ? R : never;

export type PromiseType<T> = T extends Promise<infer U> ? U : T;

export type FirstArgument<T> = T extends (first: infer F, ...args: any[]) => any ? F : never;

export type AllArguments<T> = T extends (...args: infer A) => any ? A : never;

export type ArrayElement<T> = T extends (infer U)[] ? U : never;

export type ExtractEventType<T> = T extends EventHandler<infer E> ? E : never;

export type UserReturn = ReturnTypeOf<typeof createUser>;
export type FetchReturn = PromiseType<ReturnType<typeof fetchData<{ data: string }>>>;

export type ConstructorParameters<T> = T extends new (...args: infer P) => any ? P : never;

export type InstanceType<T> = T extends new (...args: any[]) => infer I ? I : never;

type UnpackPromise<T> = T extends Promise<infer U>
    ? U extends Promise<infer V>
        ? UnpackPromise<V>
        : U
    : T;

export type DeepPromise = UnpackPromise<Promise<Promise<Promise<string>>>>;
""",
        },
        must_include=["infer_types.ts", "infer"],
        must_not_include=["ts_garbage_marker_010"],
        commit_message="Add infer keyword usage",
    ),
]

ALL_FRONTEND_CASES = REACT_TEST_CASES + REDUX_TEST_CASES + VUE_TEST_CASES + ANGULAR_TEST_CASES + TYPESCRIPT_TYPE_SYSTEM_CASES


@pytest.mark.parametrize("case", ALL_FRONTEND_CASES, ids=lambda c: c.name)
def test_frontend_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
