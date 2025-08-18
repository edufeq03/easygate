// static/js/form_dinamico.js

document.addEventListener('DOMContentLoaded', function() {
    // 1. Obter referências aos elementos do HTML
    const condominioSelect = document.getElementById('condominio-select');
    const unidadeLabel = document.getElementById('unidade-label');
    const unidadeField = document.getElementById('unidade-field');

    // 2. Função para atualizar o texto do campo
    async function atualizarCampoUnidade() {
        const condominioId = condominioSelect.value;
        
        // Verifica se um condomínio válido foi selecionado
        if (!condominioId || condominioId === '-1') {
            unidadeLabel.textContent = 'Apartamento';
            unidadeField.placeholder = '';
            return;
        }

        // 3. Fazer uma requisição para a rota da API no Flask
        try {
            // AQUI ESTÁ A ÚNICA MUDANÇA: ADICIONAR credentials: 'include'
            const response = await fetch(`/api/condominio_tipo/${condominioId}`, {
                credentials: 'include'
            });
            const data = await response.json();
            
            // 4. Mudar o rótulo e o placeholder com base na resposta
            if (data.tipo === 'casas') {
                unidadeLabel.textContent = 'Casa (Ex: Casa 5)';
                unidadeField.placeholder = 'Ex: Casa 5';
            } else { // Assume 'predio' como padrão
                unidadeLabel.textContent = 'Apartamento (Ex: Bloco A, 101)';
                unidadeField.placeholder = 'Ex: Bloco A, 101';
            }

        } catch (error) {
            console.error('Erro ao buscar o tipo de condomínio:', error);
            unidadeLabel.textContent = 'Apartamento'; // Voltar para o padrão em caso de erro
        }
    }

    // 5. Adicionar um "ouvinte" de eventos para a seleção do condomínio
    condominioSelect.addEventListener('change', atualizarCampoUnidade);

    // Chamar a função uma vez ao carregar a página para garantir que o campo esteja correto
    // se o formulário já tiver um valor pré-selecionado
    atualizarCampoUnidade();
});