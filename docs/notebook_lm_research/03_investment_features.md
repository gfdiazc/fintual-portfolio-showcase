La estrategia de inversión de Fintual es altamente cuantitativa y está diseñada para ofrecer portafolios diversificados y automatizados, enfocándose en un objetivo de **retorno absoluto**,.

A continuación, se detalla la información sobre las *features* de inversión basadas en la documentación de Fintual:

### 1. Capacidades de rebalanceo y optimización de portafolios

Fintual no se basa en la selección activa de activos ni en la predicción del mercado (*market timing*), sino en una estrategia de **inversión pasiva** y diversificada con reglas transparentes,. La optimización y el rebalanceo se gestionan a través de sus algoritmos y el equipo de inversiones para asegurar que la cartera se adhiera al modelo ideal:

*   **Rebalanceo y Ajuste Discrecional:** Una vez que se construye el "portafolio modelo" (ideal), el operador o *portfolio manager* (parte del equipo de inversiones) es el encargado de **ajustar los porcentajes de los activos financieros** de las carteras para **seguir al portafolio modelo de la mejor manera posible**,. El *portfolio manager* tiene la discrecionalidad de elegir momentos adecuados para operar la compra y venta de activos,.
*   **Seguimiento Diario:** Los equipos de inversiones y riesgos son responsables de realizar un **seguimiento diario** de las estrategias para verificar que se estén ejecutando correctamente y que se mantengan dentro de los límites internos y normativos vigentes,.
*   **Automatización de Estrategias:** La plataforma tecnológica de Fintual permite a los usuarios **automatizar sus propios procesos** relacionados con la inversión, tales como **programar estrategias de inversión recurrentes** y crear varios objetivos de inversión en paralelo,.
*   **Límites Duros de Riesgo:** La arquitectura incluye restricciones obligatorias para mitigar riesgos, como exigir que **al menos el 50% de cada portafolio contenga activos de alta liquidez**,, y aplicar **límites duros de diversificación** por compañías o emisores,.

### 2. Métricas financieras calculadas y mostradas a los usuarios

Fintual se centra en simplificar la comprensión del estado de la inversión para el usuario final, proporcionando métricas clave de forma clara:

*   **Balance:** Es el **valor actual del dinero** a la fecha de actualización,,,.
*   **Depositado Neto:** Representa **la suma de todos los depósitos menos los retiros** que el usuario ha realizado,,,.
*   **Ganado (*Earned*):** Es la **diferencia entre el Balance y el Depositado Neto**,,,.
*   **Activos Administrados (NAV):** La cifra mostrada en la aplicación bajo la sección "Actualmente administramos" corresponde al **patrimonio de los fondos mutuos** hasta el último cierre contable,,.
*   **Métricas APV (Ahorro Previsional Voluntario):** En el caso de las inversiones APV, la plataforma detalla al usuario **cuánto puso, cuánto puso el Estado, cuánto tiene, cuánto ha ganado y cuánto le falta** para aprovechar al máximo el beneficio tributario anual,.
*   **Rentabilidad Histórica:** Los usuarios pueden revisar las **rentabilidades históricas** y los **valores cuotas** de los fondos,.

### 3. Definición y generación del "optimal_portfolio" (Portafolio Modelo)

El "portafolio modelo" de Fintual es el resultado de un proceso avanzado de **optimización de portafolios** basado en décadas de investigación sobre la teoría moderna de portafolios, incluyendo el trabajo de Harry Markowitz, premio Nobel,,.

**Definición del Objetivo:**

El objetivo del algoritmo es encontrar un vector de ponderadores (porcentaje de cada activo) que sea capaz de **optimizar el retorno esperado del portafolio, sujeto a restringir el riesgo** bajo una medida de riesgo particular,. Estos portafolios se diseñan para tener objetivos de **retorno absoluto**, buscando retornos finales lo más altos posibles, de cara al cliente, de acuerdo con un límite de riesgo determinado (en lugar de ser objetivos relativos a un índice de referencia o *benchmark*),,.

**Medida de Riesgo Principal:**

Fintual utiliza y pondera con mayor peso el **Conditional Value-at-risk (CVaR)** (o *expected shortfall*) como su medida de riesgo principal en la construcción de portafolios,,. El CVaR se considera una **medida de riesgo "coherente"** (cumple con propiedades matemáticas deseables, a diferencia de la volatilidad y el Value-at-Risk [VaR]), ya que mide el nivel de pérdida que coincide con la **media de los valores contenidos bajo el α-percentil**,,,.

**Algoritmos y Enfoques Utilizados:**

Fintual utiliza principalmente dos métodos de optimización que se ayudan del **muestreo Monte Carlo** para superar las inestabilidades y los supuestos de distribución normal del modelo clásico de Markowitz,,,:

1.  **Optimización de portafolios del tipo Markowitz según un muestreo del tipo Monte Carlo:** Esta técnica realiza optimizaciones cuadráticas sucesivas a través de varias muestras distintas del vector de retornos y la matriz de covarianza para obtener un **promedio de varios portafolios óptimos**,.
2.  **Optimización de portafolios usando el CVaR como medida de riesgo y un muestreo del tipo Monte Carlo:** Este método considera el CVaR como medida de riesgo y resuelve el problema de optimización mediante el muestreo Monte Carlo como un problema equivalente, **lineal y de gran tamaño**, que es factible de resolver con métodos de optimización numérica modernos,. Además, este enfoque no asume ninguna normalidad en los retornos,.

El proceso se complementa con **restricciones cualitativas** internas del equipo de inversiones, que acotan la exposición a ciertos activos (positiva o negativamente) para inducir diversificación o eliminar activos con malas perspectivas, independientemente de los resultados del algoritmo,.