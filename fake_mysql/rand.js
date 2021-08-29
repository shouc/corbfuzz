
export const addQuery = (query) => {
    return [0, {}];
}

export const askForField = async (seed, seedIndex, field) => {
    return `${seed};${Math.random() < 0.5 ? 0 : 1};1`;
}

export const notifyType = (seed, seedIndex, typeS, field_c) => {

}
